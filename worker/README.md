# HVIE private reconstruction worker — queue-control milestone

This API is a private, local-first control plane. It is not deployed and must not be exposed to the public internet.

## Implemented
- Bearer-token protected job intake, inspection, worker claims, heartbeats, failure reporting and operator cancellation.
- JPEG, PNG and WebP content validation; image contents are decoded rather than trusting MIME types.
- Minimum 12 photos, maximum 50 photos, 25 MiB per photo, 500 MiB per job and a 60-megapixel per-image safety ceiling.
- Minimum decoded image dimensions of 1000 × 650 and SHA-256 duplicate detection.
- Server-generated filenames and UUID job directories.
- SQLite-backed transactional queue with atomic claims, expiring leases, worker identity binding and bounded retries (3 attempts).
- Lease tokens are stored as SHA-256 hashes, not plaintext.
- Database and uploaded files remain under private local storage.

## API routes
All routes except GET /health require Authorization: Bearer <HVIE_WORKER_TOKEN>.
- POST /v1/jobs — multipart form fields: project_name, vehicle_category and at least 12 photos.
- GET /v1/jobs/{job_id} — inspect job and queue state.
- POST /v1/worker/claim — JSON worker_id and optional lease_seconds (30–900).
- POST /v1/worker/heartbeat?job_id=... — JSON worker_id, lease_token and optional lease_seconds.
- POST /v1/worker/fail?job_id=... — JSON worker_id, lease_token and error; retries until attempt limit.
- POST /v1/jobs/{job_id}/cancel — JSON optional reason; cancels queued or running work and invalidates its lease.

Expired leases are re-queued while attempts remain; otherwise the job becomes failed. A worker with an expired or replaced lease cannot renew or report failure using its old token.

## Explicit limitations
- These endpoints are queue-control primitives only; no background worker process is connected yet.
- No COLMAP command is executed and no reconstruction output is produced.
- There is intentionally no completion endpoint. A job must not be marked complete until real reconstruction produces validated artifacts.
- No customer accounts, multi-tenant authorization, retention policy, malware scanning or encrypted remote storage.
- Do not store real customer photographs on a shared/public host until those controls exist.

## Local development
Use Python 3.11 or newer.
1. Install dependencies from requirements.txt.
2. Set HVIE_WORKER_TOKEN to a long random secret and HVIE_PRIVATE_STORAGE to a private directory outside the repository.
3. Run locally on loopback only: uvicorn app.main:app --host 127.0.0.1 --port 8787.
4. Run tests from this directory with pytest -q.

Never bind this API to 0.0.0.0 or deploy it publicly at this stage. The browser preview remains a static frontend and does not send photos to this API.
