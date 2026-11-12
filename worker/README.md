# HVIE local reconstruction worker

This folder contains the private Python intake API, SQLite-backed job state, COLMAP runner, Docker image, Compose definition and tests.

**Security posture:** local development only. Do not expose the API to the public internet or use it for real customer uploads.

## Components
- `app/main.py`: FastAPI intake and job/worker endpoints; Pillow-based image validation; private job directories, manifests and SQLite queue.
- `app/runner.py`: local worker process; direct SQLite queue claims; lease heartbeats; COLMAP subprocess orchestration; logs and result checks.
- `tests/test_intake.py`: API, validation, queue, lease, retry and cancellation tests.
- `tests/test_runner.py`: runner orchestration tests using a fake COLMAP executable.
- `Dockerfile`: Ubuntu 24.04 image with pinned CPU-only COLMAP package and Python dependencies.
- `compose.yaml`: loopback-bound API and worker sharing a private Docker volume.
- `.env.example`: placeholder environment settings; never put a real secret in Git.
- `requirements.txt`: pinned Python dependencies.

## Current implementation

The API accepts authenticated multipart photo uploads and validates JPEG, PNG and WebP content. Limits currently include 50 files, 25 MiB per file, 500 MiB total and 60 megapixels per image. It rejects duplicate image content using SHA-256, generates server-side filenames, and stores job manifests and files under the private storage root.

The SQLite queue supports transactional claims, expiring leases, heartbeats, bounded retries (3 attempts), failure reporting and cancellation. The runner claims jobs directly from the same SQLite database, verifies lease ownership, writes per-job logs, terminates work after cancellation or lease loss, and checks for a sparse model containing `cameras.bin`, `images.bin` and `points3D.bin`.

**Important integration gap:** the API exposes worker claim/heartbeat/fail endpoints, while `app/runner.py` currently performs its own direct SQLite claims and lease heartbeats. These are two ways of interacting with the queue, not a fully unified remote-worker protocol. Consolidate and test this boundary before scaling or deploying separate services.

## COLMAP processing stages

### Sparse (initial target)
1. `feature_extractor`
2. `exhaustive_matcher`
3. `mapper`

A valid sparse result is a camera/pose/3D-point reconstruction. It is not a dense surface mesh and not an editable car.

### Dense (not enabled / not validated)
The code contains an optional sequence:
1. `image_undistorter`
2. `patch_match_stereo`
3. `stereo_fusion`
4. `poisson_mesher`

The Dockerfile installs Ubuntu 24.04's `colmap=3.9.1-2build2` package, which is CPU-only. COLMAP PatchMatch dense stereo requires a CUDA-enabled COLMAP build and compatible NVIDIA GPU. The Compose configuration sets `HVIE_ENABLE_DENSE=0` and `HVIE_COLMAP_USE_GPU=0`. Do not enable dense processing in this image. A future GPU build or CPU-capable alternative must be evaluated, licensed, built and tested before changing this default.

A PLY header check confirms only that a file looks structurally like a PLY file. It does not prove geometric quality, complete surfaces, texture quality, watertightness or suitability for editing.

## Local container setup

1. Copy `.env.example` to `.env` in this folder.
2. Replace the placeholder `HVIE_WORKER_TOKEN` with a long random secret.
3. Set `HVIE_PRIVATE_STORAGE` to a private local path where appropriate for the chosen run mode.
4. Never commit `.env`, uploaded photos, private job data, logs or generated assets.
5. Keep the API bound to loopback. The Compose port mapping is `127.0.0.1:8787:8787`.

The root documentation [docs/WINDOWS_LOCAL_SETUP.md](../docs/WINDOWS_LOCAL_SETUP.md) describes the current laptop-first setup. Docker is optional for the first Python tests and may be memory-heavy on an 8 GB laptop.

## Environment settings

| Variable | Meaning | Current default / rule |
|---|---|---|
| `HVIE_WORKER_TOKEN` | API bearer token | Must be replaced locally; never commit |
| `HVIE_PRIVATE_STORAGE` | Private job storage directory | Compose uses `/data` |
| `COLMAP_BIN` | COLMAP executable | `colmap` |
| `HVIE_WORKER_ID` | Worker identifier | Generated if omitted |
| `HVIE_COLMAP_USE_GPU` | GPU feature extraction/matching | `0` by default |
| `HVIE_ENABLE_DENSE` | Dense reconstruction sequence | `0`; unsupported in current CPU image |
| `HVIE_WORKER_POLL_SECONDS` | Queue idle polling interval | `10` seconds |

## Test evidence and limitations

The runner tests use a generated fake executable to simulate COLMAP command success/failure and output files. They test orchestration behavior, not the real COLMAP binary, photogrammetry, dense reconstruction or vehicle quality. Run `pytest -q` from this folder after installing `requirements.txt`; record the actual result and environment. The GitHub Actions workflow also builds the CPU image and checks command help/imports, but command-help checks do not validate an actual photo reconstruction.

## Not implemented

- Frontend-to-API upload integration.
- Unified API/worker protocol for distributed execution.
- Real vehicle photo-set reconstruction proof.
- Supported dense pipeline.
- Vehicle-specific mesh cleanup and part segmentation.
- Component hierarchy/pivots and materials.
- GLB/glTF export.
- Three.js editor and asset delivery.
- Production identity, multi-tenant isolation, encrypted remote storage, retention/deletion, malware scanning and public upload protections.

Do not market this worker as a production customer-upload service or as a completed photo-to-editable-car engine.
