from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import shutil
import sqlite3
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from pydantic import BaseModel, Field
from PIL import Image, UnidentifiedImageError

MAX_FILES = 50
MAX_FILE_BYTES = 25 * 1024 * 1024
MAX_TOTAL_BYTES = 500 * 1024 * 1024
MAX_PIXELS = 60_000_000
MAX_ATTEMPTS = 3
DEFAULT_LEASE_SECONDS = 180
MAX_LEASE_SECONDS = 900
ALLOWED_FORMATS = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}
CHUNK_SIZE = 1024 * 1024


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(value: datetime) -> str:
    return value.isoformat()


def safe_label(value: str, limit: int = 100) -> str:
    return re.sub(r"[^a-zA-Z0-9 _.-]", "", value).strip()[:limit]


def token_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class WorkerIdentity(BaseModel):
    worker_id: str = Field(min_length=3, max_length=80, pattern=r"^[a-zA-Z0-9._-]+$")
    lease_token: str = Field(min_length=32, max_length=128)


class ClaimRequest(BaseModel):
    worker_id: str = Field(min_length=3, max_length=80, pattern=r"^[a-zA-Z0-9._-]+$")
    lease_seconds: int = Field(default=DEFAULT_LEASE_SECONDS, ge=30, le=MAX_LEASE_SECONDS)


class LeaseRequest(WorkerIdentity):
    lease_seconds: int = Field(default=DEFAULT_LEASE_SECONDS, ge=30, le=MAX_LEASE_SECONDS)


class FailRequest(WorkerIdentity):
    error: str = Field(min_length=1, max_length=1000)


class CancelRequest(BaseModel):
    reason: str = Field(default="Cancelled by operator", max_length=500)


def create_app(api_token: str | None = None, storage_root: Path | None = None) -> FastAPI:
    token = api_token if api_token is not None else os.getenv("HVIE_WORKER_TOKEN", "")
    root = Path(storage_root or os.getenv("HVIE_PRIVATE_STORAGE", "./private-data")).resolve()
    root.mkdir(parents=True, exist_ok=True)
    try:
        root.chmod(0o700)
    except OSError:
        pass
    database = root / "queue.sqlite3"

    def connect() -> sqlite3.Connection:
        connection = sqlite3.connect(database, timeout=15, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 15000")
        return connection

    with connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                attempt_count INTEGER NOT NULL DEFAULT 0,
                max_attempts INTEGER NOT NULL DEFAULT 3,
                worker_id TEXT,
                lease_hash TEXT,
                lease_expires_at TEXT,
                last_error TEXT,
                cancel_reason TEXT
            )
        """)
        db.execute("CREATE INDEX IF NOT EXISTS jobs_claim_idx ON jobs(status, created_at)")

    app = FastAPI(
        title="HVIE Private Reconstruction Worker API",
        version="0.2.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    async def require_token(authorization: Annotated[str | None, Header()] = None) -> None:
        if not token:
            raise HTTPException(status_code=503, detail="Worker authentication is not configured")
        supplied = authorization or ""
        if not supplied.startswith("Bearer ") or not hmac.compare_digest(supplied[7:], token):
            raise HTTPException(status_code=401, detail="Invalid worker credentials")

    def job_directory(job_id: str) -> Path:
        try:
            normalized = str(uuid.UUID(job_id))
        except ValueError:
            raise HTTPException(status_code=404, detail="Job not found")
        directory = (root / normalized).resolve()
        if directory.parent != root or not directory.is_dir():
            raise HTTPException(status_code=404, detail="Job not found")
        return directory

    def public_job(job_id: str) -> dict:
        directory = job_directory(job_id)
        manifest_path = directory / "manifest.json"
        if not manifest_path.is_file():
            raise HTTPException(status_code=404, detail="Job not found")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        with connect() as db:
            row = db.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Job not found")
        manifest.update({
            "status": row["status"],
            "updated_at": row["updated_at"],
            "queue": {
                "attempt_count": row["attempt_count"],
                "max_attempts": row["max_attempts"],
                "worker_id": row["worker_id"],
                "lease_expires_at": row["lease_expires_at"],
                "last_error": row["last_error"],
                "cancel_reason": row["cancel_reason"],
            },
        })
        return manifest

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "hvie-private-worker-api", "mode": "private-queue-no-reconstruction"}

    @app.post("/v1/jobs", status_code=202, dependencies=[Depends(require_token)])
    async def create_job(
        project_name: Annotated[str, Form()],
        vehicle_category: Annotated[str, Form()],
        photos: Annotated[list[UploadFile], File()],
    ) -> dict:
        project = safe_label(project_name)
        category = safe_label(vehicle_category, 60)
        if not project:
            raise HTTPException(status_code=422, detail="A valid project name is required")
        if not category:
            raise HTTPException(status_code=422, detail="A valid vehicle category is required")
        if not photos or len(photos) < 12:
            raise HTTPException(status_code=422, detail="At least 12 photographs are required")
        if len(photos) > MAX_FILES:
            raise HTTPException(status_code=413, detail=f"Maximum {MAX_FILES} photographs per job")

        job_id = str(uuid.uuid4())
        staging = Path(tempfile.mkdtemp(prefix=f".{job_id}-", dir=root))
        photo_dir = staging / "photos"
        photo_dir.mkdir()
        seen_hashes: set[str] = set()
        entries: list[dict] = []
        total_bytes = 0

        try:
            for index, upload in enumerate(photos, start=1):
                digest = hashlib.sha256()
                temp_path = staging / f"upload-{index}.part"
                size = 0
                with temp_path.open("wb") as target:
                    while True:
                        chunk = await upload.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        size += len(chunk)
                        total_bytes += len(chunk)
                        if size > MAX_FILE_BYTES:
                            raise HTTPException(status_code=413, detail=f"Photo {index} exceeds 25 MiB")
                        if total_bytes > MAX_TOTAL_BYTES:
                            raise HTTPException(status_code=413, detail="Job exceeds 500 MiB total")
                        digest.update(chunk)
                        target.write(chunk)

                file_hash = digest.hexdigest()
                if file_hash in seen_hashes:
                    raise HTTPException(status_code=422, detail=f"Duplicate photograph detected at position {index}")
                seen_hashes.add(file_hash)

                try:
                    with Image.open(temp_path) as image:
                        image_format = image.format
                        width, height = image.size
                        image.verify()
                except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
                    raise HTTPException(status_code=415, detail=f"Photo {index} is not a valid supported image")

                if image_format not in ALLOWED_FORMATS:
                    raise HTTPException(status_code=415, detail=f"Photo {index} must be JPEG, PNG or WebP")
                if width * height > MAX_PIXELS:
                    raise HTTPException(status_code=413, detail=f"Photo {index} exceeds the 60-megapixel safety limit")
                if width < 1000 or height < 650:
                    raise HTTPException(status_code=422, detail=f"Photo {index} must be at least 1000 × 650 pixels")

                filename = f"photo-{index:03d}{ALLOWED_FORMATS[image_format]}"
                temp_path.replace(photo_dir / filename)
                entries.append({
                    "filename": filename,
                    "sha256": file_hash,
                    "bytes": size,
                    "width": width,
                    "height": height,
                    "format": image_format,
                })
                await upload.close()

            timestamp = iso(utc_now())
            manifest = {
                "schema_version": 2,
                "job_id": job_id,
                "project_name": project,
                "vehicle_category": category,
                "status": "queued",
                "stage": "intake_validated",
                "created_at": timestamp,
                "updated_at": timestamp,
                "processing": {
                    "engine": "not_started",
                    "reconstruction_started": False,
                    "note": "Queued for a worker. No photogrammetry command has been executed.",
                },
                "photos": entries,
            }
            (staging / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            final_dir = root / job_id
            staging.replace(final_dir)
            try:
                with connect() as db:
                    db.execute(
                        "INSERT INTO jobs(job_id,status,created_at,updated_at,max_attempts) VALUES(?,?,?,?,?)",
                        (job_id, "queued", timestamp, timestamp, MAX_ATTEMPTS),
                    )
            except Exception:
                shutil.rmtree(final_dir, ignore_errors=True)
                raise
            return {
                "job_id": job_id,
                "status": "queued",
                "photo_count": len(entries),
                "message": "Capture accepted into private local storage and queued. Reconstruction has not started.",
            }
        except Exception:
            shutil.rmtree(staging, ignore_errors=True)
            raise
        finally:
            for upload in photos:
                if not upload.file.closed:
                    await upload.close()

    @app.get("/v1/jobs/{job_id}", dependencies=[Depends(require_token)])
    async def get_job(job_id: str) -> dict:
        return public_job(job_id)

    @app.post("/v1/worker/claim", dependencies=[Depends(require_token)])
    async def claim_job(request: ClaimRequest) -> dict:
        now = utc_now()
        expires = now + timedelta(seconds=request.lease_seconds)
        lease = secrets.token_urlsafe(36)
        with connect() as db:
            db.execute("BEGIN IMMEDIATE")
            expired = db.execute(
                "SELECT job_id, attempt_count, max_attempts FROM jobs WHERE status='running' AND lease_expires_at <= ?",
                (iso(now),),
            ).fetchall()
            for row in expired:
                next_status = "queued" if row["attempt_count"] < row["max_attempts"] else "failed"
                db.execute(
                    """UPDATE jobs SET status=?, worker_id=NULL, lease_hash=NULL, lease_expires_at=NULL,
                       updated_at=?, last_error=? WHERE job_id=? AND status='running'""",
                    (next_status, iso(now), "Worker lease expired", row["job_id"]),
                )
            row = db.execute(
                "SELECT job_id, attempt_count, max_attempts FROM jobs WHERE status='queued' ORDER BY created_at LIMIT 1"
            ).fetchone()
            if row is None:
                db.execute("COMMIT")
                return {"status": "idle", "message": "No queued jobs are available"}
            attempt = row["attempt_count"] + 1
            updated = db.execute(
                """UPDATE jobs SET status='running', attempt_count=?, worker_id=?, lease_hash=?,
                   lease_expires_at=?, updated_at=?, last_error=NULL
                   WHERE job_id=? AND status='queued'""",
                (attempt, request.worker_id, token_hash(lease), iso(expires), iso(now), row["job_id"]),
            )
            if updated.rowcount != 1:
                db.execute("ROLLBACK")
                raise HTTPException(status_code=409, detail="Job claim conflict; retry claim")
            db.execute("COMMIT")
        manifest = public_job(row["job_id"])
        return {
            "status": "claimed",
            "job_id": row["job_id"],
            "worker_id": request.worker_id,
            "lease_token": lease,
            "lease_expires_at": iso(expires),
            "attempt": attempt,
            "max_attempts": row["max_attempts"],
            "photo_files": [photo["filename"] for photo in manifest["photos"]],
            "note": "Lease acquired. Reconstruction execution is not connected in this milestone.",
        }

    def validate_lease(db: sqlite3.Connection, identity: WorkerIdentity) -> sqlite3.Row:
        row = db.execute("SELECT * FROM jobs WHERE job_id=?", (identity_job_id,)).fetchone()
        return row

    @app.post("/v1/worker/heartbeat", dependencies=[Depends(require_token)])
    async def heartbeat(job_id: str, request: LeaseRequest) -> dict:
        now = utc_now()
        expires = now + timedelta(seconds=request.lease_seconds)
        with connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
            if row is None:
                db.execute("ROLLBACK")
                raise HTTPException(status_code=404, detail="Job not found")
            valid = (
                row["status"] == "running"
                and row["worker_id"] == request.worker_id
                and row["lease_hash"] == token_hash(request.lease_token)
                and row["lease_expires_at"] is not None
                and row["lease_expires_at"] > iso(now)
            )
            if not valid:
                db.execute("ROLLBACK")
                raise HTTPException(status_code=409, detail="Worker lease is invalid or expired")
            db.execute(
                "UPDATE jobs SET lease_expires_at=?, updated_at=? WHERE job_id=?",
                (iso(expires), iso(now), job_id),
            )
            db.execute("COMMIT")
        return {"status": "running", "job_id": job_id, "lease_expires_at": iso(expires)}

    @app.post("/v1/worker/fail", dependencies=[Depends(require_token)])
    async def fail_job(job_id: str, request: FailRequest) -> dict:
        now = utc_now()
        with connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
            if row is None:
                db.execute("ROLLBACK")
                raise HTTPException(status_code=404, detail="Job not found")
            valid = (
                row["status"] == "running"
                and row["worker_id"] == request.worker_id
                and row["lease_hash"] == token_hash(request.lease_token)
                and row["lease_expires_at"] is not None
                and row["lease_expires_at"] > iso(now)
            )
            if not valid:
                db.execute("ROLLBACK")
                raise HTTPException(status_code=409, detail="Worker lease is invalid or expired")
            next_status = "queued" if row["attempt_count"] < row["max_attempts"] else "failed"
            db.execute(
                """UPDATE jobs SET status=?, worker_id=NULL, lease_hash=NULL, lease_expires_at=NULL,
                   last_error=?, updated_at=? WHERE job_id=?""",
                (next_status, request.error.strip(), iso(now), job_id),
            )
            db.execute("COMMIT")
        return {"job_id": job_id, "status": next_status, "retry_scheduled": next_status == "queued"}

    @app.post("/v1/jobs/{job_id}/cancel", dependencies=[Depends(require_token)])
    async def cancel_job(job_id: str, request: CancelRequest) -> dict:
        now = iso(utc_now())
        with connect() as db:
            result = db.execute(
                """UPDATE jobs SET status='cancelled', worker_id=NULL, lease_hash=NULL,
                   lease_expires_at=NULL, cancel_reason=?, updated_at=?
                   WHERE job_id=? AND status IN ('queued','running')""",
                (request.reason.strip() or "Cancelled by operator", now, job_id),
            )
            if result.rowcount == 0:
                exists = db.execute("SELECT status FROM jobs WHERE job_id=?", (job_id,)).fetchone()
                if exists is None:
                    raise HTTPException(status_code=404, detail="Job not found")
                raise HTTPException(status_code=409, detail=f"Job cannot be cancelled from status {exists['status']}")
        return {"job_id": job_id, "status": "cancelled"}

    return app


app = create_app()
