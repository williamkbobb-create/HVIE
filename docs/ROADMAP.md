# HVIE roadmap

The roadmap is evidence-gated. A later milestone does not start merely because the UI can display a placeholder.

## Milestone 0 — Reproducible local development

**Goal:** another developer can install dependencies, run tests and understand the current state.

Acceptance:
- Windows/Python environment recorded.
- Existing pytest suite runs and exact result is documented.
- COLMAP version and executable verified on the chosen local environment.
- Git branch and commit recorded.
- No secrets or photo data committed.

## Milestone 1 — Real sparse reconstruction proof

**Goal:** one real vehicle photo set produces a valid COLMAP sparse model.

Acceptance:
- Use a controlled non-customer image set with adequate overlap.
- Actual COLMAP executable runs all sparse stages.
- Registered camera count and sparse point output are recorded.
- Expected model files exist and can be opened/inspected.
- Logs, runtime, hardware and failures are recorded.
- No claim of dense or editable output.

## Milestone 2 — Dense geometry and texture strategy

**Goal:** choose and prove a technically viable dense reconstruction route.

Options to evaluate:
- CUDA-enabled COLMAP build on compatible NVIDIA hardware.
- Open-source CPU-capable alternatives, assessed for vehicle quality, memory, runtime and licence.

Acceptance:
- Build/install reproducible.
- Real photo set produces a dense surface/point cloud.
- Mesh opens in an independent viewer.
- Reflective panels, glass, dark paint, holes and missing surfaces reviewed.
- Resource requirements and failure cases documented.

## Milestone 3 — Vehicle mesh processing

**Goal:** turn raw geometry into a usable vehicle asset.

Acceptance:
- Mesh cleanup and scale/coordinate conventions defined.
- Outlier/noise and hole handling documented.
- Texture pipeline and material limitations assessed.
- Source provenance and confidence/missing regions retained.

## Milestone 4 — Vehicle-specific segmentation

**Goal:** selectable semantic vehicle components.

Acceptance:
- Labelled test vehicles and component taxonomy exist.
- Doors, hood/bonnet, trunk/boot, bumpers, wheels, tyres, glass, lights and interior regions are evaluated.
- Segmentation accuracy is measured and manual correction supported.
- Components have stable names and transforms/pivots.

## Milestone 5 — GLB asset contract

**Goal:** portable 3D vehicle asset.

Acceptance:
- GLB/glTF export and import validated in independent tools.
- Hierarchy, transforms, materials and textures preserved.
- File-size and geometry budgets defined.
- Version and provenance metadata included.

## Milestone 6 — Three.js editor

**Goal:** edit the actual reconstructed model in the browser.

Acceptance:
- Load a generated GLB, not a hard-coded placeholder.
- Orbit, pan, zoom and reset camera.
- Select actual components by name.
- Apply material/paint and supported wheel/interior changes.
- Save and reload project versions.
- Clear distinction between editable, inferred and unsegmented geometry.

## Milestone 7 — Secure product integration

**Goal:** connect the browser workflow to the processing backend safely.

Acceptance:
- Frontend uploads through authenticated API.
- Project/job ownership and authorization enforced.
- Job progress, cancellation, errors and output delivery work end-to-end.
- Encrypted remote storage, retention/deletion, malware scanning, quotas and abuse protection implemented.
- API is not publicly exposed until security review passes.

## Milestone 8 — Production readiness

**Goal:** reliable, maintainable service.

Acceptance:
- Load and reliability tests.
- Backup/restore and retention procedures.
- Monitoring, alerting and operational runbooks.
- Deployment and rollback process.
- Costs and compute limits approved by project owner.
