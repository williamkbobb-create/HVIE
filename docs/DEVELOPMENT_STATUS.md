# HVIE development status

**Last documented snapshot:** 2026-11-12. This is a repository handover snapshot, not a live CI/deployment monitor. Re-check GitHub Actions, Render and the local machine before relying on runtime status.

## Status legend

- **Implemented in code:** tracked implementation exists.
- **Simulated/test harness:** tests exercise a mock or fake dependency, not the real external engine.
- **Not verified:** code/config exists but no reliable runtime evidence is recorded here.
- **Not implemented:** no functional implementation exists.

## Product and engineering status

| Area | Status | Evidence / qualification |
|---|---|---|
| Standalone React/TypeScript/Vite frontend | Implemented in code | `src/App.tsx`, `src/main.tsx`, `src/styles.css` |
| Multi-photo selection and previews | Implemented in code | Browser-only File objects and object URLs |
| Eight exterior angle labels | Implemented in code | Coverage UI and per-photo selector |
| Initial intake checks | Implemented in code | 12 photos, 8 views, minimum dimensions; not photogrammetry QA |
| Frontend-to-API upload | Not implemented | UI explicitly says files remain in browser |
| FastAPI private intake | Implemented in code; runtime not verified here | `worker/app/main.py` |
| Image content checks and duplicate hashes | Implemented in code | Pillow and SHA-256 in API |
| Private job directory and manifest | Implemented in code | Backend storage code |
| SQLite queue, lease, retries, cancellation | Implemented in code | API and runner logic; integration boundary needs consolidation |
| COLMAP sparse runner | Implemented in code; real engine not verified | Runner invokes feature extraction, matching and mapper |
| Runner unit tests | Simulated/test harness | Fake COLMAP executable; not actual reconstruction |
| Docker image | Configuration exists; build/runtime not verified here | Ubuntu 24.04, pinned CPU-only COLMAP package |
| GitHub Actions workflow | Configuration exists; latest run must be checked | pytest + Docker/CLI smoke check |
| Real vehicle sparse reconstruction | Not verified / not yet proven | No real photo-set result recorded |
| Dense COLMAP reconstruction | Not supported by current image | Requires CUDA-enabled COLMAP + compatible NVIDIA GPU |
| Dense CPU alternative | Not implemented | Research and benchmark required |
| Mesh cleanup and texture QA | Not implemented | — |
| Vehicle part segmentation | Not implemented | — |
| GLB/glTF export | Not implemented | — |
| Three.js vehicle viewer/editor | Not implemented | Dependency only |
| Production customer security | Not implemented | No auth identities, tenant isolation, encrypted remote storage, retention or malware scanning |

## Known gaps to resolve

1. **Frontend/API integration:** build a secure upload flow, job creation, progress/status and result delivery. Do not expose the local API publicly.
2. **Queue protocol:** API worker endpoints exist while runner directly manipulates SQLite. Choose one explicit contract and test it.
3. **Real COLMAP verification:** build the image and run the actual executable, not only command-help checks.
4. **Real sparse reconstruction:** test a small, controlled vehicle photo set and inspect camera registration and point-cloud quality.
5. **Dense strategy:** do not enable current dense flags. Evaluate GPU build or CPU alternative separately.
6. **Windows development path:** establish Python environment on the user's Windows 11, 8 GB RAM laptop; identify GPU before making hardware decisions.

## Evidence recording template

For every test, record:
- date and commit SHA;
- OS, CPU, RAM and GPU;
- Python and COLMAP versions;
- exact test command or workflow run link;
- input photo count and source (test-only, non-customer);
- exit code and relevant logs;
- output artifacts and file sizes;
- visual inspection outcome;
- known failures and next action.

Do not change a row to “verified” without this evidence.
