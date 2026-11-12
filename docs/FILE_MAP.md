# HVIE repository file map

This index is intended to help a new developer or AI find the real source files quickly. It lists tracked files present in the repository snapshot reviewed on 2026-11-12. Always compare against the live branch tree before editing.

## Root

| Path | Purpose |
|---|---|
| `.gitignore` | Excludes dependencies, build output, environment files, virtual environments, caches and local worker data |
| `index.html` | Vite browser entry HTML |
| `package.json` | Frontend scripts and dependencies |
| `tsconfig.json` | TypeScript compiler configuration |
| `vite.config.ts` | Vite React plugin/build configuration |
| `README.md` | Main project and AI handover entry point |

## Frontend — `src/`

| Path | Purpose |
|---|---|
| `src/main.tsx` | React application bootstrap |
| `src/App.tsx` | Main capture workspace, photo selection, previews, angle assignment and initial validation |
| `src/styles.css` | Responsive dark automotive workspace styles |

## Worker — `worker/`

| Path | Purpose |
|---|---|
| `worker/README.md` | Worker-specific setup, queue, COLMAP and limitation notes |
| `worker/Dockerfile` | Ubuntu 24.04 CPU-only COLMAP + Python image |
| `worker/compose.yaml` | Local API/worker services and private shared volume |
| `worker/.dockerignore` | Files excluded from Docker build context |
| `worker/.env.example` | Placeholder local environment variables; no real secrets |
| `worker/.gitignore` | Worker-local ignore rules |
| `worker/requirements.txt` | Pinned FastAPI, Uvicorn, multipart, Pillow, pytest and httpx dependencies |
| `worker/app/__init__.py` | Python package marker |
| `worker/app/main.py` | FastAPI intake, authentication, image validation, job manifests and queue endpoints |
| `worker/app/runner.py` | Local queue runner, COLMAP commands, leases, cancellation, logs and output validation |
| `worker/tests/test_intake.py` | API, image validation, queue, lease, retry and cancellation tests |
| `worker/tests/test_runner.py` | Runner orchestration tests using a fake COLMAP executable |

## CI — `.github/`

| Path | Purpose |
|---|---|
| `.github/workflows/worker-tests.yml` | GitHub Actions worker tests, Docker image build and COLMAP CLI smoke checks |

## Project documentation — `docs/`

| Path | Purpose |
|---|---|
| `docs/PROJECT_HANDOVER.md` | Mission, vision, history, current state and next steps |
| `docs/ARCHITECTURE.md` | System components, data flow and boundaries |
| `docs/RECONSTRUCTION_PIPELINE.md` | Capture, sparse/dense reconstruction and later geometry stages |
| `docs/DEVELOPMENT_STATUS.md` | Implemented vs simulated vs unverified vs missing |
| `docs/WINDOWS_LOCAL_SETUP.md` | Current Windows 11 / 8 GB laptop setup |
| `docs/ROADMAP.md` | Milestones and acceptance criteria |
| `docs/FILE_MAP.md` | Repository source-file index |
| `docs/ENGINEERING_RULES.md` | Safety, privacy, branch, cost and evidence rules |

## Files that should remain local and untracked

- `worker/.env` and any other real secret files.
- `worker/private-data/`, SQLite job databases and uploaded photos.
- COLMAP databases, sparse/dense outputs and generated PLY/GLB files.
- Python virtual environments, caches, node_modules and build output.

If a new file is added or a file is renamed, update this map and the root README links.
