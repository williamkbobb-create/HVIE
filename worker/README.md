# HVIE local reconstruction worker

The worker is local-first and must not be exposed to the public internet. It reads the same private storage directory and SQLite queue used by the private intake API.

## Implemented queue and runner
- Transactional SQLite claims with expiring worker leases and SHA-256 hashed lease tokens.
- Lease heartbeats during long-running COLMAP commands and ownership checks before commands and final completion.
- Cancellation detection: the runner checks queue state and terminates its active COLMAP process if an operator cancels the job.
- Bounded retries (3 attempts), failure logging and job manifests.
- Safe subprocess execution with argument arrays (no shell), per-job logs and a six-hour default command timeout.
- Sparse SfM pipeline: feature extraction, exhaustive matching and incremental mapper.
- Optional dense pipeline: image undistortion, PatchMatch stereo, stereo fusion and Poisson meshing. Dense completion is withheld unless a PLY mesh header is readable.

## Start locally
Use Python 3.11+ and install requirements.txt. Configure:
- HVIE_WORKER_TOKEN: long random secret for the private intake API.
- HVIE_PRIVATE_STORAGE: same private directory for API and worker, outside the repository.
- COLMAP_BIN: executable path or command name (default colmap).
- HVIE_WORKER_ID: optional stable worker identifier.
- HVIE_COLMAP_USE_GPU: default 0; set to 1 only when CUDA/GPU support is confirmed.
- HVIE_ENABLE_DENSE: default 0; set to 1 only after sparse reconstruction has been validated and the host has sufficient resources.
- HVIE_WORKER_POLL_SECONDS: queue idle polling interval (default 10 seconds).

Run the private API on loopback: uvicorn app.main:app --host 127.0.0.1 --port 8787.
Run the worker in another process: python -m app.runner.

## Job results
- sparse_complete: COLMAP produced a sparse model containing cameras.bin, images.bin and points3D.bin.
- dense_complete: the dense commands ran and a PLY mesh header was validated. Visual quality and suitability for editing still require review.
- queued or failed: processing failed; see last_error and logs/colmap.log.

A sparse model is not a dense surface mesh and is not an editable vehicle. Dense reconstruction can struggle with glossy paint, glass, low-texture panels and incomplete camera coverage. No part segmentation, component pivots, materials, GLB export or browser editor integration is implemented yet.

Never bind the API to 0.0.0.0 or deploy it publicly at this stage. No paid API or hosted reconstruction service is used.
