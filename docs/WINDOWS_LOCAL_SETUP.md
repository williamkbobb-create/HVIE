# HVIE local setup — Windows 11

## Current developer machine

- Operating system: Windows 11.
- RAM: 8 GB.
- Graphics adapter: not yet identified.
- First goal: Python worker tests and a small CPU sparse reconstruction.
- Do not assume Docker or CUDA is installed.
- Do not attempt dense COLMAP on the current CPU-only container.

## Phase A — Install the basic tools

1. Install Python 3.11 from the [official Python release page](https://www.python.org/downloads/release/python-3119/).
2. In the installer, enable **Add python.exe to PATH**.
3. Install Git for Windows from [git-scm.com](https://git-scm.com/install/windows).
4. Open Windows Terminal or PowerShell.
5. Check versions:

```powershell
py --version
git --version
```

Expected: Python 3.11.x and a Git version. If `py` is not recognised, reopen Terminal after installation or repair the Python PATH setting.

## Phase B — Identify graphics adapter

1. Press Windows + X and open Device Manager.
2. Expand **Display adapters**.
3. Record the exact adapter name(s), including whether it says NVIDIA, AMD or Intel.
4. Do not install CUDA until an NVIDIA adapter and its supported compute capability/driver are confirmed.

## Phase C — Obtain the correct repository branch

Use the repository:
- https://github.com/williamkbobb-create/HVIE
- Branch: `feature/standalone-app-foundation`

Keep work on this branch. Do not clone or copy another HackyTech project into this repository. Keep customer images and generated outputs outside the repository.

A developer can use GitHub Desktop if a graphical workflow is preferred. If using Git in PowerShell, the minimal sequence is:

```powershell
git clone --branch feature/standalone-app-foundation https://github.com/williamkbobb-create/HVIE.git
cd HVIE
```

If repository access requires authentication, use GitHub's approved sign-in flow; never paste a password or token into chat or commit it to a file.

## Phase D — Create an isolated Python environment

From the repository folder:

```powershell
py -3.11 -m venv worker\.venv
worker\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r worker\requirements.txt
```

If PowerShell blocks activation, do not weaken machine-wide execution policy. Use a one-session approved activation approach or run the environment's Python executable directly.

Run the worker tests from the worker folder:

```powershell
cd worker
python -m pytest -q
```

Record the exact test output. Tests that use a fake COLMAP executable validate runner control flow, not real photogrammetry.

## Phase E — COLMAP availability

The current Dockerfile installs Ubuntu 24.04's pinned CPU-only COLMAP package. That Linux package is not automatically installed on native Windows.

Before choosing a local COLMAP installation method:
1. Confirm Windows version and CPU architecture.
2. Identify the graphics adapter.
3. Check free disk space.
4. Decide whether to use a supported native Windows COLMAP build or WSL2/Linux. On an 8 GB laptop, avoid adding Docker Desktop and WSL overhead until needed.
5. Verify the actual executable and version before processing photos.

Do not assume the Docker image has been built or run just because the Dockerfile exists.

## Phase F — First real-photo experiment

Use a small, non-customer set of photos of one stationary vehicle. Keep the originals backed up. Avoid a huge set on the 8 GB machine.

Start with the sparse pipeline only:
- feature extraction;
- exhaustive matching;
- incremental mapping.

Check:
- whether images register;
- number of registered cameras;
- number/distribution of sparse points;
- whether the model has `cameras.bin`, `images.bin` and `points3D.bin`;
- whether the reconstruction is visually coherent;
- peak memory, elapsed time and errors.

A successful sparse run is only a first geometry milestone. It is not a complete car mesh, texture or editable model.

## Resource guidance for 8 GB RAM

- Close memory-heavy applications before processing.
- Start with a modest photo set and lower image dimensions only for controlled experiments; retain original files.
- Avoid running the frontend build, Docker build and reconstruction simultaneously.
- Monitor Task Manager memory and disk activity.
- Do not purchase a GPU or subscribe to a hosted API for this first milestone.
- Dense reconstruction is deferred until hardware and algorithm choice are established.

## Security

- Never commit `.env`, API tokens, uploaded photos, private-data folders, logs or generated meshes.
- Keep the local API bound to 127.0.0.1.
- Do not use customer photos for initial tests.
- Do not expose the worker/API to the public internet.
