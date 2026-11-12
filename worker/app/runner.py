from __future__ import annotations

import hashlib
import json
import os
import secrets
import shutil
import signal
import sqlite3
import subprocess
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Sequence

LEASE_SECONDS = 180
HEARTBEAT_SECONDS = 20
MAX_ATTEMPTS = 3


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def stamp(value: datetime) -> str:
    return value.isoformat()


def digest_token(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def connect(database: Path) -> sqlite3.Connection:
    db = sqlite3.connect(database, timeout=15, isolation_level=None)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA busy_timeout=15000")
    return db


@contextmanager
def db_session(database: Path):
    db = connect(database)
    try:
        yield db
    finally:
        db.close()


def claim_job(database: Path, worker_id: str, lease_seconds: int = LEASE_SECONDS) -> dict | None:
    now = now_utc()
    expires = now + timedelta(seconds=lease_seconds)
    lease = secrets.token_urlsafe(36)
    with db_session(database) as db:
        db.execute("BEGIN IMMEDIATE")
        expired = db.execute(
            "SELECT job_id,attempt_count,max_attempts FROM jobs "
            "WHERE status='running' AND lease_expires_at <= ?",
            (stamp(now),),
        ).fetchall()
        for row in expired:
            next_status = "queued" if row["attempt_count"] < row["max_attempts"] else "failed"
            db.execute(
                "UPDATE jobs SET status=?,worker_id=NULL,lease_hash=NULL,lease_expires_at=NULL,"
                "updated_at=?,last_error=? WHERE job_id=? AND status='running'",
                (next_status, stamp(now), "Worker lease expired", row["job_id"]),
            )
        row = db.execute(
            "SELECT job_id,attempt_count,max_attempts FROM jobs "
            "WHERE status='queued' ORDER BY created_at LIMIT 1"
        ).fetchone()
        if row is None:
            db.execute("COMMIT")
            return None
        attempt = row["attempt_count"] + 1
        result = db.execute(
            "UPDATE jobs SET status='running',attempt_count=?,worker_id=?,lease_hash=?,"
            "lease_expires_at=?,updated_at=?,last_error=NULL WHERE job_id=? AND status='queued'",
            (attempt, worker_id, digest_token(lease), stamp(expires), stamp(now), row["job_id"]),
        )
        if result.rowcount != 1:
            db.execute("ROLLBACK")
            return None
        db.execute("COMMIT")
    return {
        "job_id": row["job_id"],
        "worker_id": worker_id,
        "lease_token": lease,
        "attempt": attempt,
        "max_attempts": row["max_attempts"],
        "lease_expires_at": stamp(expires),
    }


def owns_lease(database: Path, lease: dict) -> bool:
    with db_session(database) as db:
        row = db.execute("SELECT * FROM jobs WHERE job_id=?", (lease["job_id"],)).fetchone()
    return bool(
        row
        and row["status"] == "running"
        and row["worker_id"] == lease["worker_id"]
        and row["lease_hash"] == digest_token(lease["lease_token"])
        and row["lease_expires_at"]
        and row["lease_expires_at"] > stamp(now_utc())
    )


def heartbeat(database: Path, lease: dict, lease_seconds: int = LEASE_SECONDS) -> bool:
    now = now_utc()
    expires = now + timedelta(seconds=lease_seconds)
    with db_session(database) as db:
        result = db.execute(
            "UPDATE jobs SET lease_expires_at=?,updated_at=? WHERE job_id=? AND status='running' "
            "AND worker_id=? AND lease_hash=? AND lease_expires_at>?",
            (
                stamp(expires), stamp(now), lease["job_id"], lease["worker_id"],
                digest_token(lease["lease_token"]), stamp(now),
            ),
        )
    return result.rowcount == 1


def write_manifest(job_dir: Path, update: dict) -> None:
    path = job_dir / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest.update(update)
    manifest["updated_at"] = stamp(now_utc())
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    temporary.replace(path)


def valid_sparse_model(path: Path) -> bool:
    required = ("cameras.bin", "images.bin", "points3D.bin")
    return path.is_dir() and all((path / name).is_file() and (path / name).stat().st_size > 0 for name in required)


def find_sparse_model(sparse_root: Path) -> Path | None:
    candidates = [path for path in sparse_root.iterdir() if path.is_dir() and valid_sparse_model(path)] if sparse_root.exists() else []
    return max(candidates, key=lambda path: path.stat().st_mtime) if candidates else None


def sparse_command_plan(colmap_bin: str, job_dir: Path, use_gpu: bool) -> list[tuple[str, list[str]]]:
    images = job_dir / "photos"
    database = job_dir / "database.db"
    sparse = job_dir / "sparse"
    return [
        ("feature_extraction", [
            colmap_bin, "feature_extractor", "--database_path", str(database),
            "--image_path", str(images), "--FeatureExtraction.use_gpu", "1" if use_gpu else "0",
        ]),
        ("feature_matching", [
            colmap_bin, "exhaustive_matcher", "--database_path", str(database),
            "--FeatureMatching.use_gpu", "1" if use_gpu else "0",
        ]),
        ("sparse_mapping", [
            colmap_bin, "mapper", "--database_path", str(database),
            "--image_path", str(images), "--output_path", str(sparse),
        ]),
    ]


def dense_command_plan(colmap_bin: str, job_dir: Path, model: Path) -> list[tuple[str, list[str]]]:
    images = job_dir / "photos"
    dense_dir = job_dir / "dense"
    return [
        ("image_undistortion", [
            colmap_bin, "image_undistorter", "--image_path", str(images),
            "--input_path", str(model), "--output_path", str(dense_dir),
            "--output_type", "COLMAP", "--max_image_size", "2000",
        ]),
        ("patch_match_stereo", [
            colmap_bin, "patch_match_stereo", "--workspace_path", str(dense_dir),
            "--workspace_format", "COLMAP", "--PatchMatchStereo.geom_consistency", "true",
        ]),
        ("stereo_fusion", [
            colmap_bin, "stereo_fusion", "--workspace_path", str(dense_dir),
            "--workspace_format", "COLMAP", "--input_type", "geometric",
            "--output_path", str(dense_dir / "fused.ply"),
        ]),
        ("poisson_meshing", [
            colmap_bin, "poisson_mesher", "--input_path", str(dense_dir / "fused.ply"),
            "--output_path", str(dense_dir / "meshed-poisson.ply"),
        ]),
    ]


def valid_ply_mesh(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size < 32:
        return False
    try:
        with path.open("rb") as stream:
            header = stream.read(65536).split(b"end_header", 1)
        if len(header) != 2:
            return False
        text = header[0].decode("ascii", errors="strict")
        return text.startswith("ply") and "format " in text and "element vertex " in text
    except (OSError, UnicodeDecodeError):
        return False


def run_command(
    command: Sequence[str],
    log_path: Path,
    database: Path,
    lease: dict,
    timeout_seconds: int,
) -> None:
    if not owns_lease(database, lease):
        raise RuntimeError("Worker lease is no longer active before command start")
    started = time.monotonic()
    next_heartbeat = started + HEARTBEAT_SECONDS
    with log_path.open("a", encoding="utf-8") as log:
        log.write("\n$ " + " ".join(command) + "\n")
        log.flush()
        process = subprocess.Popen(
            list(command),
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
        )
        while process.poll() is None:
            if time.monotonic() - started > timeout_seconds:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                raise TimeoutError(f"COLMAP command exceeded {timeout_seconds} seconds")
            if time.monotonic() >= next_heartbeat:
                if not heartbeat(database, lease):
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=15)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
                    raise RuntimeError("Worker lease was lost; command terminated")
                next_heartbeat = time.monotonic() + HEARTBEAT_SECONDS
            with db_session(database) as db:
                row = db.execute("SELECT status FROM jobs WHERE job_id=?", (lease["job_id"],)).fetchone()
            if row is None or row["status"] == "cancelled":
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                raise RuntimeError("Job was cancelled; command terminated")
            time.sleep(1)
        if process.returncode != 0:
            raise RuntimeError(f"COLMAP command failed with exit code {process.returncode}")


def finish_job(database: Path, job_dir: Path, lease: dict, status: str, artifacts: dict) -> None:
    now = stamp(now_utc())
    with db_session(database) as db:
        db.execute("BEGIN IMMEDIATE")
        result = db.execute(
            "UPDATE jobs SET status=?,worker_id=NULL,lease_hash=NULL,lease_expires_at=NULL,updated_at=?,last_error=NULL "
            "WHERE job_id=? AND status='running' AND worker_id=? AND lease_hash=? AND lease_expires_at>?",
            (status, now, lease["job_id"], lease["worker_id"], digest_token(lease["lease_token"]), now),
        )
        if result.rowcount != 1:
            db.execute("ROLLBACK")
            raise RuntimeError("Could not commit reconstruction result: worker no longer owns the job lease")
        db.execute("COMMIT")
    write_manifest(job_dir, {
        "status": status,
        "stage": status,
        "processing": {
            "engine": "COLMAP",
            "reconstruction_started": True,
            "completed_at": now,
            "worker_id": lease["worker_id"],
            "attempt": lease["attempt"],
            "artifacts": artifacts,
            "note": "Sparse structure-from-motion completed. This is not yet a segmented, editable vehicle model.",
        },
    })


def fail_job(database: Path, lease: dict, error: str) -> None:
    now = stamp(now_utc())
    with db_session(database) as db:
        row = db.execute("SELECT attempt_count,max_attempts,status FROM jobs WHERE job_id=?", (lease["job_id"],)).fetchone()
        if not row or row["status"] != "running":
            return
        status = "queued" if row["attempt_count"] < row["max_attempts"] else "failed"
        db.execute(
            "UPDATE jobs SET status=?,worker_id=NULL,lease_hash=NULL,lease_expires_at=NULL,updated_at=?,last_error=? "
            "WHERE job_id=? AND status='running' AND worker_id=? AND lease_hash=?",
            (
                status, now, error[:1000], lease["job_id"], lease["worker_id"],
                digest_token(lease["lease_token"]),
            ),
        )


def run_one_job(
    storage_root: Path,
    colmap_bin: str = "colmap",
    worker_id: str = "hvie-local-worker",
    use_gpu: bool = False,
    dense: bool = False,
    timeout_seconds: int = 6 * 60 * 60,
) -> str:
    root = storage_root.resolve()
    database = root / "queue.sqlite3"
    lease = claim_job(database, worker_id)
    if lease is None:
        return "idle"
    job_dir = (root / lease["job_id"]).resolve()
    if job_dir.parent != root or not job_dir.is_dir():
        fail_job(database, lease, "Private job directory is missing or invalid")
        return "failed"

    logs = job_dir / "logs"
    logs.mkdir(exist_ok=True)
    log_path = logs / "colmap.log"
    try:
        if shutil.which(colmap_bin) is None and not Path(colmap_bin).is_file():
            raise FileNotFoundError(f"COLMAP executable not found: {colmap_bin}")
        images = job_dir / "photos"
        photo_count = len([p for p in images.iterdir() if p.is_file()]) if images.is_dir() else 0
        if photo_count < 12:
            raise RuntimeError("Job has fewer than 12 stored photographs")
        write_manifest(job_dir, {
            "status": "running",
            "stage": "worker_started",
            "processing": {
                "engine": "COLMAP",
                "reconstruction_started": True,
                "worker_id": worker_id,
                "attempt": lease["attempt"],
                "note": "Local COLMAP process started; no editable vehicle parts are generated at this stage.",
            },
        })
        for stage, command in sparse_command_plan(colmap_bin, job_dir, use_gpu):
            write_manifest(job_dir, {
                "status": "running",
                "stage": stage,
                "processing": {
                    "engine": "COLMAP",
                    "reconstruction_started": True,
                    "current_stage": stage,
                    "worker_id": worker_id,
                    "attempt": lease["attempt"],
                    "log_file": "logs/colmap.log",
                },
            })
            run_command(command, log_path, database, lease, timeout_seconds)

        model = find_sparse_model(job_dir / "sparse")
        if model is None:
            raise RuntimeError("COLMAP finished without a valid sparse model (cameras.bin, images.bin, points3D.bin)")
        artifacts = {
            "sparse_model": str(model.relative_to(job_dir)),
            "sparse_model_files": ["cameras.bin", "images.bin", "points3D.bin"],
            "log": "logs/colmap.log",
            "dense_mesh": None,
        }
        result_status = "sparse_complete"
        if dense:
            for stage, command in dense_command_plan(colmap_bin, job_dir, model):
                write_manifest(job_dir, {
                    "status": "running",
                    "stage": stage,
                    "processing": {
                        "engine": "COLMAP",
                        "reconstruction_started": True,
                        "current_stage": stage,
                        "worker_id": worker_id,
                        "attempt": lease["attempt"],
                        "log_file": "logs/colmap.log",
                    },
                })
                run_command(command, log_path, database, lease, timeout_seconds)
            mesh = job_dir / "dense" / "meshed-poisson.ply"
            if not valid_ply_mesh(mesh):
                raise RuntimeError("Dense pipeline ended without a readable PLY mesh")
            artifacts["dense_mesh"] = str(mesh.relative_to(job_dir))
            result_status = "dense_complete"

        finish_job(database, job_dir, lease, result_status, artifacts)
        return result_status
    except Exception as exc:
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"\nHVIE worker error: {type(exc).__name__}: {exc}\n")
        fail_job(database, lease, f"{type(exc).__name__}: {exc}")
        try:
            with db_session(database) as db:
                state = db.execute("SELECT status FROM jobs WHERE job_id=?", (lease["job_id"],)).fetchone()
            actual_status = state["status"] if state else "failed"
            write_manifest(job_dir, {
                "status": actual_status,
                "stage": "cancelled" if actual_status == "cancelled" else "worker_failed",
                "processing": {
                    "engine": "COLMAP",
                    "reconstruction_started": True,
                    "worker_id": worker_id,
                    "attempt": lease["attempt"],
                    "error": f"{type(exc).__name__}: {exc}",
                    "log_file": "logs/colmap.log",
                },
            })
        except Exception:
            pass
        return "failed"


def main() -> None:
    root = Path(os.getenv("HVIE_PRIVATE_STORAGE", "./private-data"))
    worker_id = os.getenv("HVIE_WORKER_ID", f"worker-{uuid.uuid4().hex[:10]}")
    colmap_bin = os.getenv("COLMAP_BIN", "colmap")
    use_gpu = os.getenv("HVIE_COLMAP_USE_GPU", "0").lower() in {"1", "true", "yes"}
    dense = os.getenv("HVIE_ENABLE_DENSE", "0").lower() in {"1", "true", "yes"}
    poll_seconds = max(2, int(os.getenv("HVIE_WORKER_POLL_SECONDS", "10")))
    print(f"HVIE worker {worker_id} starting; storage={root.resolve()}; dense={dense}; gpu={use_gpu}")
    while True:
        result = run_one_job(root, colmap_bin, worker_id, use_gpu, dense)
        if result == "idle":
            time.sleep(poll_seconds)
        else:
            print(f"Job processing result: {result}")


if __name__ == "__main__":
    main()
