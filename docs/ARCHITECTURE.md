# HVIE architecture

## Current logical architecture

```text
Browser (React + TypeScript + Vite)
  └── capture workspace
      ├── vehicle project metadata
      ├── photo selection / preview
      ├── angle assignment / coverage
      └── initial local validation
          [API upload integration not implemented]
                    |
                    v
Private FastAPI intake API (Python)
  ├── bearer-token authentication
  ├── Pillow image validation
  ├── SHA-256 duplicate detection
  ├── server-generated file names
  ├── private job directory + manifest.json
  └── SQLite queue
          |
          v
Local reconstruction runner (Python)
  ├── transactional job claim
  ├── expiring lease + heartbeat
  ├── cancellation / retry / failure state
  ├── COLMAP subprocesses
  ├── per-job logs
  └── sparse model validation
          |
          v
Future geometry pipeline
  ├── dense reconstruction / texture
  ├── mesh cleanup
  ├── vehicle-part segmentation
  ├── component transforms / materials
  └── GLB/glTF export
          |
          v
Future Three.js editor
  ├── inspect / orbit / zoom
  ├── select component
  ├── edit material and supported properties
  └── save project version
```

The diagram shows the intended product flow. Dashed/explicitly marked future stages are not implemented.

## Frontend

- Entry: `src/main.tsx`.
- Main UI: `src/App.tsx`.
- Styles: `src/styles.css`.
- Build tooling: Vite and TypeScript.
- Three.js is a package dependency only; there is no current viewer integration.

The frontend currently stores selected File objects and preview object URLs in browser memory. It does not persist a project, upload images, poll job status or display a reconstruction result.

## API and intake

- Entry/app factory: `worker/app/main.py`.
- FastAPI and Uvicorn serve the local API.
- Pillow decodes uploaded files and validates actual content rather than trusting only file extensions.
- The API uses a bearer token from `HVIE_WORKER_TOKEN`.
- It writes private job files and a manifest, and records job state in SQLite.
- Compose publishes the API only on loopback (127.0.0.1).

Review `worker/app/main.py` for the authoritative route and schema details.

## Queue and worker

- Runner: `worker/app/runner.py`.
- SQLite claims are transactional.
- A worker lease includes a worker identity and secret token; only a hash is stored.
- Leases expire and are renewed by heartbeats.
- Retry attempts are bounded (three).
- Cancellation or lease loss terminates the active subprocess.
- Per-job logs are written to `logs/colmap.log`.

**Important integration issue:** the API has worker claim/heartbeat/fail routes, while the current runner claims and renews jobs directly in SQLite. This is not yet a unified remote worker protocol. Keep both local-only until the boundary is deliberately consolidated and tested.

## Storage layout (logical)

A job storage root contains:
- `queue.sqlite3`: job queue/state.
- `<job-id>/photos/`: validated uploaded photos.
- `<job-id>/manifest.json`: project, photo and processing state.
- `<job-id>/logs/colmap.log`: reconstruction command log.
- `<job-id>/database.db`: COLMAP database.
- `<job-id>/sparse/`: COLMAP sparse model folders.
- `<job-id>/dense/`: future/optional dense workspace and mesh outputs.

Keep this storage outside Git and private. Do not upload customer photos or generated data into repository commits.

## Local container setup

`worker/Dockerfile` pins Ubuntu 24.04 and COLMAP package 3.9.1-2build2. `worker/compose.yaml` defines API and worker containers sharing one named private volume. The API is loopback-bound. The current image is CPU-only; dense is disabled.

## Intended future separation

For a first local proof, a single machine and private local storage are sufficient. Later, if processing is separated from the API, define an explicit authenticated worker protocol, object-storage contract, lease renewal, result upload, cancellation and idempotency before adding multiple worker machines. Do not scale an unclear job lifecycle.
