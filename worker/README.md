# HVIE local reconstruction worker

The worker is local-first and must not be exposed to the public internet. It reads the same private storage directory and SQLite queue used by the private intake API.

## Queue and execution
- Transactional SQLite claims with expiring worker leases and SHA-256 hashed lease tokens.
- Lease heartbeats during long-running COLMAP commands and ownership checks before commands and final completion.
- Cancellation detection terminates the active COLMAP process and preserves the cancelled state.
- Bounded retries (3 attempts), failure logging and job manifests.
- Safe subprocess execution with argument arrays (no shell), per-job logs and a six-hour default command timeout.
- Sparse SfM pipeline: feature extraction, exhaustive matching and incremental mapper.
- Optional dense pipeline: image undistortion, PatchMatch stereo, stereo fusion and Poisson meshing. Dense completion is withheld unless a PLY mesh header is readable.

## Local container environment
The Docker image uses Ubuntu 24.04 and pins the repository package COLMAP 3.9.1-2build2. This distribution package is CPU-only; GPU support is intentionally disabled. Dense reconstruction is also disabled by default.

Compose starts two local services sharing one private Docker volume: the authenticated intake API and the COLMAP worker. The API port is published only on 127.0.0.1. Create a local .env from .env.example and replace the placeholder token with a long random secret before starting the stack. Never commit the real .env file.

The container stack is a local development foundation, not a hosted deployment. It has no customer identity system, multi-tenant isolation, encrypted remote storage, retention controls or public upload protections. Do not expose the API or use it for real customer uploads yet.

## Environment settings
- HVIE_WORKER_TOKEN: long random secret for the private intake API.
- HVIE_PRIVATE_STORAGE: same private directory for API and worker; Compose sets this to /data.
- COLMAP_BIN: executable path or command name (default colmap).
- HVIE_WORKER_ID: optional stable worker identifier.
- HVIE_COLMAP_USE_GPU: default 0; enable only on a separately validated CUDA build and compatible GPU.
- HVIE_ENABLE_DENSE: default 0; enable only after sparse reconstruction is validated and the host has sufficient resources.
- HVIE_WORKER_POLL_SECONDS: queue idle polling interval (default 10 seconds).

## Job results
- sparse_complete: COLMAP produced a sparse model containing cameras.bin, images.bin and points3D.bin.
- dense_complete: dense commands ran and a PLY mesh header was validated. Visual quality and suitability for editing still require review.
- queued or failed: processing failed; inspect last_error and logs/colmap.log.

A sparse model is not a dense surface mesh and is not an editable vehicle. Dense reconstruction can struggle with glossy paint, glass, low-texture panels and incomplete camera coverage. No part segmentation, component pivots, materials, GLB export or browser editor integration is implemented yet.

No paid reconstruction API or hosted reconstruction service is used.
