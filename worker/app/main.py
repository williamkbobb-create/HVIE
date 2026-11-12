from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

MAX_FILES = 50
MAX_FILE_BYTES = 25 * 1024 * 1024
MAX_TOTAL_BYTES = 500 * 1024 * 1024
MAX_PIXELS = 60_000_000
ALLOWED_FORMATS = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}
CHUNK_SIZE = 1024 * 1024


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_label(value: str, limit: int = 100) -> str:
    value = re.sub(r"[^a-zA-Z0-9 _.-]", "", value).strip()
    return value[:limit]


def create_app(api_token: str | None = None, storage_root: Path | None = None) -> FastAPI:
    token = api_token if api_token is not None else os.getenv("HVIE_WORKER_TOKEN", "")
    root = Path(storage_root or os.getenv("HVIE_PRIVATE_STORAGE", "./private-data")).resolve()
    root.mkdir(parents=True, exist_ok=True)

    app = FastAPI(
        title="HVIE Private Reconstruction Worker API",
        version="0.1.0",
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

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "hvie-private-worker-api", "mode": "intake-only"}

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
                final_path = photo_dir / filename
                temp_path.replace(final_path)
                entries.append({
                    "filename": filename,
                    "sha256": file_hash,
                    "bytes": size,
                    "width": width,
                    "height": height,
                    "format": image_format,
                })
                await upload.close()

            manifest = {
                "schema_version": 1,
                "job_id": job_id,
                "project_name": project,
                "vehicle_category": category,
                "status": "queued",
                "stage": "intake_validated",
                "created_at": utc_now(),
                "updated_at": utc_now(),
                "processing": {
                    "engine": "not_started",
                    "reconstruction_started": False,
                    "note": "Intake only. No photogrammetry command has been executed.",
                },
                "photos": entries,
            }
            (staging / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            final_dir = root / job_id
            staging.replace(final_dir)
            return {
                "job_id": job_id,
                "status": "queued",
                "photo_count": len(entries),
                "message": "Capture accepted into private local storage. Reconstruction has not started.",
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
        try:
            normalized = str(uuid.UUID(job_id))
        except ValueError:
            raise HTTPException(status_code=404, detail="Job not found")
        job_dir = (root / normalized).resolve()
        if job_dir.parent != root or not job_dir.is_dir():
            raise HTTPException(status_code=404, detail="Job not found")
        manifest_path = job_dir / "manifest.json"
        if not manifest_path.is_file():
            raise HTTPException(status_code=404, detail="Job not found")
        return json.loads(manifest_path.read_text(encoding="utf-8"))

    return app


app = create_app()
