# HackyTech Vehicle Intelligence Engine (HVIE)

> **Mission:** turn photographs of a real vehicle into a faithful, inspectable and ultimately editable 3D vehicle asset — using an engineering pipeline HackyTech can understand, operate and improve itself.

HVIE is a standalone HackyTech product. It is not the Lavage Tracker, not a generic 3D viewer, and not a service that substitutes a stock/cartoon car for the customer's photographed vehicle. The long-term goal is a vehicle-focused digital workspace in which the reconstructed vehicle can be inspected and its supported components and materials edited independently.

**Repository:** [williamkbobb-create/HVIE](https://github.com/williamkbobb-create/HVIE)  
**Active engineering branch:** `feature/standalone-app-foundation`  
**Preview:** [hvie-preview.onrender.com](https://hvie-preview.onrender.com) (static frontend preview; it is not proof that the reconstruction worker is deployed or connected)  
**Project status:** early foundation / reconstruction pipeline not yet validated on a real vehicle photo set.

---

## Start here — AI and developer handover

Read these documents in order before changing code:

1. [Project handover](docs/PROJECT_HANDOVER.md) — mission, history, vision, current state and continuation instructions.
2. [Architecture](docs/ARCHITECTURE.md) — frontend, API, queue, worker, storage and boundaries.
3. [Reconstruction pipeline](docs/RECONSTRUCTION_PIPELINE.md) — photo intake through COLMAP, outputs and technical constraints.
4. [Development status](docs/DEVELOPMENT_STATUS.md) — implemented, simulated, unverified and missing capabilities.
5. [Windows local setup](docs/WINDOWS_LOCAL_SETUP.md) — guided local setup for the current Windows 11 / 8 GB development laptop.
6. [Roadmap](docs/ROADMAP.md) — ordered milestones and acceptance criteria.
7. [Repository file map](docs/FILE_MAP.md) — what each tracked file and folder is for.
8. [Engineering rules](docs/ENGINEERING_RULES.md) — safety, branch, cost, privacy and truthful-status requirements.

The [worker-specific README](worker/README.md) documents the private Python worker and its environment settings.

## What HVIE is intended to become

A user photographs one real, stationary vehicle from multiple overlapping viewpoints. HVIE guides the capture, validates the incoming files, runs photogrammetry, and presents the resulting geometry for inspection. Later, vehicle-specific processing should separate meaningful components — for example doors, bonnet/hood, boot/trunk, bumpers, wheels, tyres, glass, lights, seats and interior trim — so that supported parts can be selected and edited independently.

Long-term capabilities include:
- faithful photo-derived exterior geometry and texture, with uncertainty and missing areas made visible;
- dense surface reconstruction and mesh cleanup;
- vehicle-aware part segmentation, stable component names and pivots;
- GLB/glTF export and import;
- a Three.js interactive inspection and editing workspace;
- material/paint, wheel, glass, lighting, interior and component customization;
- project history, asset versioning and eventually secure customer accounts and storage.

These are **product goals**, not claims that these features are already implemented.

## Current product flow

1. Create a vehicle project and identify the vehicle category.
2. Add multiple overlapping photographs of the same vehicle.
3. Assign views and inspect capture coverage.
4. Validate the initial capture set.
5. Upload to a private, authenticated intake API (backend exists; frontend is not connected to it yet).
6. Queue a job and let a local worker claim it.
7. Run COLMAP sparse structure-from-motion (SfM).
8. Inspect the sparse result and logs; later add a supported dense reconstruction route.
9. Clean and process geometry, segment vehicle parts, export GLB and connect the browser editor.

## Technology and languages

| Area | Technology | Purpose / current use |
|---|---|---|
| Browser application | React 18, TypeScript 5.7, Vite 6 | Capture workspace and frontend build |
| UI icons | lucide-react | Interface icons |
| 3D foundation | Three.js 0.172 | Dependency is present; an actual HVIE 3D editor is not implemented |
| Worker/API language | Python 3.11 target | Intake, job queue and reconstruction orchestration |
| API | FastAPI, Uvicorn, Pydantic | Authenticated local photo intake and job endpoints |
| Image validation | Pillow | Decode and validate uploaded image formats and dimensions |
| Queue/state | SQLite | Transactional job claims, leases, retries and job state |
| Photogrammetry | COLMAP 3.9.1-2build2 in Ubuntu 24.04 image | CPU sparse reconstruction commands; dense PatchMatch is not supported by this CPU-only build |
| Containerization | Docker, Docker Compose | Reproducible local worker/API environment |
| Automated checks | pytest, GitHub Actions | Worker tests and container/CLI smoke checks |
| Frontend hosting | Render Static Site | Browser preview only; not the reconstruction compute environment |

No paid hosted vehicle-reconstruction API is part of the design. The aim is to build and own the orchestration and vehicle-specific intelligence, while using established open-source foundations where appropriate. Review licences and operating costs before adopting additional dependencies.

## What exists now

### Browser frontend
- Dark automotive workspace built with React and TypeScript.
- Vehicle project name and category fields.
- Multi-file JPG, PNG and WebP selection, drag-and-drop, image previews and removal.
- Duplicate filtering by filename and file size within the current browser session.
- Per-photo angle assignment.
- Eight exterior coverage angles: front, front-left, left, rear-left, rear, rear-right, right and front-right.
- Initial intake checks: project name, at least 12 photos, all eight exterior angles assigned, and minimum 1000 × 650 image dimensions.
- Capture guidance and explicit notice that files remain in the browser until secure upload is connected.

These are guided intake checks, not a photogrammetry-quality guarantee. The frontend currently does **not** submit files to the API.

### Python intake API and queue
- Bearer-token-protected API.
- JPEG, PNG and WebP decoding/validation.
- File count, per-file size, total size and pixel-count limits.
- SHA-256 duplicate detection.
- Server-generated filenames and private job directories.
- JSON job manifests and SQLite queue state.
- Worker claim, heartbeat, failure/retry and cancellation endpoints.
- Lease ownership and bounded retry handling.

### Local COLMAP runner foundation
- Direct SQLite queue claim with expiring worker leases and heartbeats.
- Sparse command plan: feature extraction, exhaustive matching and incremental mapping.
- Per-job logs and manifest stage updates.
- Cancellation and lease-loss process termination.
- Sparse model output validation using the expected COLMAP binary files.
- Optional dense command plan exists in code, but must not be enabled with the current CPU-only COLMAP image.

## Critical limitations — read before claiming completion

- The frontend and API are not integrated.
- The API's claim/heartbeat endpoints and the local runner's direct SQLite claim path are separate mechanisms; the intended production/local orchestration contract still needs consolidation and end-to-end testing.
- The worker image has not been confirmed as built and executed against a real COLMAP installation in the current development environment.
- No real vehicle photograph set has yet been reconstructed and visually assessed.
- Runner tests use a fake COLMAP executable to exercise orchestration; they do not prove photogrammetry quality or real COLMAP execution.
- The current Ubuntu COLMAP package is CPU-only. Sparse SfM is the initial target. COLMAP PatchMatch dense stereo requires a CUDA-enabled COLMAP build and compatible NVIDIA GPU.
- A sparse model is not a dense mesh. A PLY mesh is not automatically a clean, watertight, textured or editable vehicle.
- No vehicle-specific part segmentation, component pivots, GLB export, materials editor or functional Three.js vehicle editor exists yet.
- No customer authentication, tenant isolation, encrypted remote object storage, retention/deletion controls, malware scanning or public upload hardening exists. Do not accept customer uploads or expose the local API publicly.
- A successful CI build or fake-runner test must never be described as a successful real-car reconstruction.

## Development sequence

**Immediate milestone:** set up the developer's Windows 11 laptop (8 GB RAM; graphics adapter not yet identified), run the existing Python tests, verify COLMAP availability and run a controlled sparse reconstruction using a small, non-customer photo set.

Then:
1. Prove real COLMAP sparse reconstruction on a real photo set and inspect the result.
2. Decide and validate a dense reconstruction strategy (CUDA COLMAP on suitable NVIDIA hardware, or a separately evaluated open-source CPU alternative).
3. Produce inspectable dense geometry and texture with quality checks.
4. Build vehicle-specific geometry cleanup and part segmentation.
5. Export and validate GLB/glTF.
6. Build the Three.js inspection/editor experience.
7. Connect secure frontend upload, job progress and result delivery.
8. Add production-grade identity, privacy, storage, retention, security and deployment controls.

See [Roadmap](docs/ROADMAP.md) for acceptance gates.

## Local development

The guided Windows instructions are in [docs/WINDOWS_LOCAL_SETUP.md](docs/WINDOWS_LOCAL_SETUP.md). Do not assume Docker, CUDA or a dense reconstruction setup is required for the first milestone. With 8 GB RAM, start with tests and a small CPU sparse reconstruction; monitor memory and avoid large photo sets.

## Repository and branch policy

- Work only in this standalone HVIE repository under the `williamkbobb-create` GitHub account.
- Continue on `feature/standalone-app-foundation` unless the project owner explicitly approves another branch.
- Do not merge to `main`, deploy a production service, change unrelated projects, or create paid infrastructure without explicit approval.
- Preserve existing code and inspect files before editing.
- Keep local secrets, customer images and reconstruction outputs out of Git.

## How to continue

An AI or developer taking over should:
1. Read the handover and engineering rules.
2. Inspect the current branch, commit history, repository tree and latest CI run rather than trusting this document as live state.
3. Confirm which changes are committed and which are only local.
4. Run the existing tests and record exact results.
5. Work on the smallest milestone that advances real photo-to-geometry proof.
6. Update the status and handover docs whenever implementation or evidence changes.

**The measure of progress is not how advanced the interface looks. It is whether HVIE can reliably turn a real set of photographs into inspectable, increasingly editable geometry.**
