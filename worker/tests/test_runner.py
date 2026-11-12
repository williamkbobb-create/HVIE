import json
import sqlite3
from pathlib import Path

from app.runner import run_one_job


def setup_job(root: Path) -> str:
    job_id = "7b2e2e6a-0a30-4f0f-8c54-4a7b1a0baf01"
    job = root / job_id
    (job / "photos").mkdir(parents=True)
    for index in range(12):
        (job / "photos" / f"photo-{index:03d}.jpg").write_bytes(b"fake-image-placeholder")
    (job / "manifest.json").write_text(json.dumps({
        "job_id": job_id,
        "status": "queued",
        "photos": [{"filename": f"photo-{index:03d}.jpg"} for index in range(12)],
    }))
    with sqlite3.connect(root / "queue.sqlite3") as db:
        db.execute("""
            CREATE TABLE jobs (
                job_id TEXT PRIMARY KEY, status TEXT NOT NULL, created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL, attempt_count INTEGER NOT NULL DEFAULT 0,
                max_attempts INTEGER NOT NULL DEFAULT 3, worker_id TEXT, lease_hash TEXT,
                lease_expires_at TEXT, last_error TEXT, cancel_reason TEXT
            )
        """)
        db.execute(
            "INSERT INTO jobs(job_id,status,created_at,updated_at,max_attempts) VALUES(?,?,?,?,3)",
            (job_id, "queued", "2026-01-01T00:00:00+00:00", "2026-01-01T00:00:00+00:00"),
        )
    return job_id


def fake_colmap(path: Path, fail_command: str | None = None) -> Path:
    executable = path / "colmap-fake"
    script = """#!/usr/bin/env python3
import pathlib, sys
command = sys.argv[1]
if command == "mapper":
    output = pathlib.Path(sys.argv[sys.argv.index("--output_path") + 1]) / "0"
    output.mkdir(parents=True, exist_ok=True)
    for name in ("cameras.bin", "images.bin", "points3D.bin"):
        (output / name).write_bytes(b"model")
"""
    if fail_command:
        script += f"if command == {fail_command!r}: sys.exit(7)\n"
    executable.write_text(script)
    executable.chmod(0o755)
    return executable


def test_local_runner_claims_and_completes_sparse_pipeline(tmp_path):
    job_id = setup_job(tmp_path)
    binary = fake_colmap(tmp_path)
    result = run_one_job(tmp_path, str(binary), worker_id="test-worker")
    assert result == "sparse_complete"
    with sqlite3.connect(tmp_path / "queue.sqlite3") as db:
        row = db.execute("SELECT status,attempt_count,worker_id FROM jobs WHERE job_id=?", (job_id,)).fetchone()
    assert row == ("sparse_complete", 1, None)
    manifest = json.loads((tmp_path / job_id / "manifest.json").read_text())
    assert manifest["processing"]["engine"] == "COLMAP"
    assert manifest["processing"]["artifacts"]["sparse_model"] == "sparse/0"
    assert (tmp_path / job_id / "logs" / "colmap.log").is_file()


def test_missing_colmap_is_reported_and_retried(tmp_path):
    job_id = setup_job(tmp_path)
    result = run_one_job(tmp_path, "/not/a/real/colmap", worker_id="test-worker")
    assert result == "failed"
    with sqlite3.connect(tmp_path / "queue.sqlite3") as db:
        status, attempts, error = db.execute(
            "SELECT status,attempt_count,last_error FROM jobs WHERE job_id=?", (job_id,)
        ).fetchone()
    assert status == "queued"
    assert attempts == 1
    assert "COLMAP executable not found" in error


def test_runner_returns_idle_without_queued_jobs(tmp_path):
    (tmp_path / "queue.sqlite3").touch()
    with sqlite3.connect(tmp_path / "queue.sqlite3") as db:
        db.execute("""
            CREATE TABLE jobs (
                job_id TEXT PRIMARY KEY, status TEXT NOT NULL, created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL, attempt_count INTEGER NOT NULL DEFAULT 0,
                max_attempts INTEGER NOT NULL DEFAULT 3, worker_id TEXT, lease_hash TEXT,
                lease_expires_at TEXT, last_error TEXT, cancel_reason TEXT
            )
        """)
    assert run_one_job(tmp_path, worker_id="test-worker") == "idle"


def test_missing_colmap_does_not_claim_reconstruction_started(tmp_path):
    job_id = setup_job(tmp_path)
    run_one_job(tmp_path, "/not/a/real/colmap", worker_id="test-worker")
    manifest = json.loads((tmp_path / job_id / "manifest.json").read_text())
    assert manifest["processing"]["reconstruction_started"] is False
    assert manifest["status"] == "queued"


def test_dense_pipeline_requires_a_readable_mesh(tmp_path):
    job_id = setup_job(tmp_path)
    binary = fake_colmap(tmp_path)
    script = binary.read_text()
    script += """ 
if command == "poisson_mesher":
    output = pathlib.Path(sys.argv[sys.argv.index("--output_path") + 1])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(b"ply\\nformat ascii 1.0\\nelement vertex 3\\nproperty float x\\nproperty float y\\nproperty float z\\nend_header\\n0 0 0\\n")
"""
    binary.write_text(script)
    binary.chmod(0o755)
    result = run_one_job(tmp_path, str(binary), worker_id="test-worker", dense=True)
    assert result == "dense_complete"
    manifest = json.loads((tmp_path / job_id / "manifest.json").read_text())
    mesh = tmp_path / job_id / manifest["processing"]["artifacts"]["dense_mesh"]
    assert mesh.is_file()
    assert mesh.read_bytes().startswith(b"ply")
