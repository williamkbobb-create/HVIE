# HVIE photo-to-3D reconstruction pipeline

## Objective

Create an accurate 3D representation from photographs of one real vehicle. Each stage must produce inspectable evidence and must not overstate what its output means.

## Stage 0 — Capture planning (partially implemented)

The current browser intake accepts JPG, PNG and WebP, displays previews, allows view labels, and checks for 12 images, eight exterior angle labels and 1000 × 650 minimum dimensions.

Capture quality still requires human and later automated review. Recommended capture:
- one stationary vehicle, unchanged during the capture session;
- diffuse, stable lighting and minimal harsh reflections;
- many overlapping images with shared visual features;
- complete walk-around, including front, rear, sides and diagonal views;
- roof, wheels, lights, windows and cabin details where accessible;
- sharp images, consistent focus and minimal motion blur;
- avoid large gaps and avoid moving people/vehicles obscuring the subject.

Twelve images are only an initial intake threshold, not a recommended universal count or guarantee. More images and good overlap are normally needed.

## Stage 1 — Secure intake (backend exists; frontend is not connected)

The API validates file type/content, dimensions and configured size limits, hashes content to detect duplicates, generates filenames and creates a private job manifest and queue record.

Current code limits: up to 50 files, 25 MiB each, 500 MiB total and 60 megapixels per image. Verify these against current source before changing or documenting new limits.

## Stage 2 — Sparse structure-from-motion (runner implemented; real-photo proof pending)

Current command sequence:
1. COLMAP feature extraction.
2. COLMAP exhaustive feature matching.
3. COLMAP incremental mapping.

Expected sparse model files:
- `cameras.bin`
- `images.bin`
- `points3D.bin`

This produces camera poses and a sparse 3D point representation. It is not a surface mesh, complete vehicle body, texture or editable part model.

## Stage 3 — Dense reconstruction (not currently supported by default)

The runner contains an optional dense command sequence:
1. image undistortion;
2. PatchMatch stereo;
3. stereo fusion;
4. Poisson meshing.

However, the current pinned COLMAP package is CPU-only. COLMAP PatchMatch dense stereo requires a CUDA-enabled COLMAP build and compatible NVIDIA GPU. The current Docker Compose configuration disables dense and GPU. Do not switch these flags on in the current image.

A separate CPU-capable dense alternative may be researched, but must be evaluated for output quality on glossy automotive surfaces, memory/runtime needs, operating-system support, licence, maintenance and export compatibility before adoption.

## Stage 4 — Mesh and texture quality (not implemented)

A future quality pipeline must assess:
- geometry completeness and scale/coordinate conventions;
- disconnected components and outliers;
- holes, non-manifold edges and self-intersections;
- surface noise and mesh density;
- texture alignment, seams and missing regions;
- glass, reflective paint, chrome and dark low-texture panels;
- unseen surfaces and areas that are inferred rather than observed.

Never imply that photogrammetry can recover hidden or unphotographed geometry with certainty. Missing areas need to be flagged, separately modelled or explicitly marked as estimated.

## Stage 5 — Vehicle-aware segmentation (not implemented)

The output needs to become a semantic vehicle asset, not just one fused mesh. Planned classes include:
- body shell and panels;
- left/right doors and door handles;
- bonnet/hood and boot/trunk/tailgate;
- front/rear bumpers, grille and mirrors;
- wheels, rims and tyres;
- windscreen, side/rear glass and lights;
- seats, dashboard and interior trim where capture supports them.

Segmentation may require a combination of geometry processing, learned segmentation, manual correction and vehicle priors. Do not promise reliable automatic part boundaries before building a labelled test set and measuring accuracy.

## Stage 6 — Asset packaging and browser editor (not implemented)

Target interchange format: GLB/glTF with:
- component hierarchy and stable names;
- transforms/pivots;
- geometry and material references;
- textures;
- source-to-output provenance and version metadata.

Three.js is already listed as a dependency, but no functional HVIE editor exists. The future editor should load a real generated GLB, support orbit/pan/zoom, select parts, apply material changes and export/save versions.

## Validation gates

A stage is complete only when evidence exists:
- **Intake:** actual API accepts/rejects test files as expected; private storage confirmed.
- **Sparse:** real COLMAP binary processes a real photo set; valid model produced; logs and visual inspection retained.
- **Dense:** supported dense engine runs on declared hardware; mesh opens in an independent viewer; quality reviewed.
- **Segmentation:** components are independently selectable and reviewed against ground truth.
- **GLB:** export opens in at least one independent GLB viewer and preserves hierarchy/materials.
- **Editor:** loads the generated asset and edits actual model components, not a placeholder.
