# HVIE private reconstruction worker — intake milestone

This is a private, local-first API foundation. It is deliberately not deployed and is not exposed to the public internet.

## Current capabilities
- Bearer-token protected job creation and job inspection.
- JPEG, PNG and WebP content validation (file contents are decoded; browser-provided MIME types are not trusted).
- Minimum 12 photos, maximum 50 photos, 25 MiB per photo and 500 MiB per job.
- Minimum decoded image dimensions of 1000 × 650.
- SHA-256 duplicate detection.
- Server-generated filenames and UUID job directories; user filenames are never used as filesystem paths.
- Private local storage under `HVIE_PRIVATE_STORAGE` (default `./private-data`).
- Atomic staging-directory promotion and JSON job manifest.
- Failed intake attempts clean up temporary files.

## Explicit limitations
- Job status remains `queued`; no queue consumer or COLMAP process is connected yet.
- No GLB export, mesh cleanup, vehicle-part segmentation, rigging or 3D editor integration.
- No customer authentication, multi-tenant ownership, retention policy, malware scanning or encrypted remote storage yet.
- Do not store real customer vehicle photographs on a shared/public host until those controls exist.
- The API token is a single operator secret, not a customer identity system.

## Local development
Use Python 3.11 or newer.

1. Install the dependencies from `requirements.txt`.
2. Set `HVIE_WORKER_TOKEN` to a long random secret and optionally set `HVIE_PRIVATE_STORAGE` to a private directory outside the repository.
3. Run locally on loopback only: `uvicorn app.main:app --host 127.0.0.1 --port 8787`.
4. Run tests from this directory with `pytest -q`.

Never bind this intake service to `0.0.0.0` or deploy it publicly at this stage. The browser preview remains a static frontend and does not send photos to this API.

## Next worker milestone
Add a bounded job-claim/lease mechanism, worker heartbeat, retry and cancellation semantics, then integrate a locally installed COLMAP executable behind a dry-run/verification gate. Do not mark a job complete until reconstruction artifacts and validation reports exist.
