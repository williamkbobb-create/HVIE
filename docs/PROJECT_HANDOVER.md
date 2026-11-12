# HVIE — project handover

## 1. Identity and mission

**Name:** HackyTech Vehicle Intelligence Engine (HVIE).  
**Owner/product family:** HackyTech.  
**Repository:** `williamkbobb-create/HVIE`.  
**Purpose:** build an owned, photo-to-3D vehicle reconstruction and editing pipeline.

HVIE should take photographs of an actual vehicle and progressively turn them into a faithful 3D asset. The goal is not to show a generic car, create a cartoon approximation, or claim that a sparse point cloud is a finished vehicle. The user wants a serious automotive technology workspace where the photographed vehicle can eventually be inspected and edited at component level.

## 2. Product vision

A user captures one stationary car from many overlapping angles. HVIE guides the capture and checks the files, reconstructs camera poses and geometry, builds a dense surface/texture, cleans the result, identifies vehicle parts, and opens the result in a browser editor.

Long-term editing targets include body panels (doors, bonnet/hood, boot/trunk, bumpers), wheels and tyres, windows and glass, lights, seats, dashboard and interior trim. Components should have meaningful names, stable transforms/pivots and editable materials. A user should be able to change paint, wheel design, trim and selected parts without destroying the source reconstruction.

This is a staged research and engineering goal. The current repository is an early foundation, not a completed reconstruction product.

## 3. What has happened so far

The initial product direction was a separate application with its own upload interface: select a vehicle photo set, submit it for processing, then display the resulting model in a dedicated workspace. The app was explicitly separated from Lavage Tracker.

A standalone React/TypeScript/Vite frontend was created with a dark automotive workspace, vehicle metadata, multi-photo upload, previews, angle assignment, eight-angle exterior coverage and initial intake validation.

A Python worker foundation was added: FastAPI authenticated intake, Pillow image validation, duplicate detection, private job directories/manifests, SQLite job state, leases, retries and cancellation. A local COLMAP runner was added with sparse reconstruction commands, logs, lease checks and output validation.

A Docker image and Compose setup were added around Ubuntu 24.04's pinned CPU-only COLMAP package. CI workflow configuration was added for pytest and a Docker/CLI smoke check.

The frontend still does not call the API. The worker image and actual COLMAP reconstruction have not yet been proven on a real vehicle photo set. Runner tests simulate COLMAP using a fake executable.

## 4. Current repository baseline

- Active branch: `feature/standalone-app-foundation`.
- Main branch is not the working branch and must remain untouched without explicit approval.
- Browser app: `src/`.
- Python service and runner: `worker/`.
- Technical docs: `docs/`.
- Render preview: https://hvie-preview.onrender.com — static frontend preview only; verify its current deployment before relying on it.

Before continuing, fetch the live repository tree and latest commit. Do not assume this document is a substitute for inspecting code.

## 5. Technology and languages

- TypeScript / TSX: browser interface and typed React components.
- JavaScript runtime / Node package tooling: Vite build and development.
- Python 3.11 target: API, queue and worker orchestration.
- FastAPI, Uvicorn, Pydantic: HTTP API and request validation.
- Pillow: image decoding and metadata/dimension validation.
- SQLite: transactional job queue and state.
- COLMAP: open-source photogrammetry / structure-from-motion foundation.
- Docker / Compose: reproducible local environment.
- Three.js: installed dependency for future browser 3D rendering; not yet integrated into a functional editor.
- pytest and GitHub Actions: automated worker checks.

No paid hosted reconstruction API is intended. Future dependencies must be assessed for licence, hardware, maintenance and operating costs.

## 6. Current engineering truth

Implemented foundations:
- Browser photo intake and capture coverage UI.
- Authenticated private API intake and image validation.
- Private local job storage and manifests.
- SQLite queue, lease and retry logic.
- Local COLMAP sparse runner orchestration.
- Docker/Compose and CI configuration.

Not proven:
- Current real COLMAP image build and execution in this development environment.
- Real-photo sparse reconstruction quality.
- Any dense reconstruction result.
- Frontend upload-to-worker integration.
- Production security or customer-data lifecycle.

Not built:
- A robust dense mesh/texture path.
- Vehicle-aware geometry cleanup and segmentation.
- Door/bonnet/boot/wheel/interior component hierarchy.
- GLB export.
- Three.js editor, component selection and material editing.

## 7. Known technical constraint

The pinned Ubuntu package is CPU-only. COLMAP feature extraction, matching and sparse mapping are the initial CPU target. COLMAP PatchMatch dense stereo requires a CUDA-enabled COLMAP build and compatible NVIDIA GPU. The current Compose environment intentionally disables GPU and dense stages.

The developer's current laptop is Windows 11 with 8 GB RAM; graphics adapter is not yet identified. This is suitable to start Python development and tests, and may handle a small CPU sparse reconstruction. It is not a reason to promise full dense reconstruction locally.

## 8. Immediate next steps

1. Complete local Windows environment setup using the guide.
2. Verify Python 3.11 and Git versions.
3. Identify the laptop graphics adapter; do not install CUDA until hardware is known.
4. Install worker dependencies in an isolated virtual environment.
5. Run pytest and record exact output.
6. Verify COLMAP installation separately.
7. Prepare a small, non-customer, overlapping vehicle photo set.
8. Run sparse reconstruction, preserve logs, and visually inspect the result.
9. Fix issues based on evidence before moving to dense reconstruction.

## 9. Rules for the next AI/developer

- Read [ENGINEERING_RULES.md](ENGINEERING_RULES.md) before changes.
- Work only in this repository and approved feature branch.
- Inspect files and current status before edits.
- Do not merge, deploy production, create paid resources or alter other projects without approval.
- Do not invent tests or report simulated tests as real reconstruction.
- Keep the original photos and intermediate artifacts traceable.
- Update [DEVELOPMENT_STATUS.md](DEVELOPMENT_STATUS.md) after each verified milestone.
