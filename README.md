# HackyTech Vehicle Intelligence Engine (HVIE)

Standalone photo-to-3D vehicle capture and customization workspace.

## Product flow
1. Create a vehicle project.
2. Upload overlapping photographs of one stationary vehicle.
3. Review capture coverage and image quality.
4. Send the capture set to a private reconstruction worker.
5. Inspect the reconstructed asset in a browser 3D workspace.
6. Customize body paint, wheels, seats, interior trim, glass and supported components.

## Current engineering milestone
The browser app provides guided capture intake and coverage review. The private Python worker provides authenticated local photo intake, image validation, duplicate detection, private job manifests, a SQLite queue, expiring worker leases, heartbeats, bounded retries and cancellation.

A local COLMAP runner is now implemented for sparse structure-from-motion and optional dense multi-view stereo. It checks the worker lease, writes per-job logs, terminates work on cancellation, validates sparse model files, and requires a readable PLY mesh header before reporting dense completion.

A CPU-only Docker environment is pinned to Ubuntu 24.04's COLMAP 3.9.1-2build2 package. The local Compose stack keeps the API bound to loopback and stores job data in a private local volume. GPU and dense processing are disabled by default.

## Important limitations
- The frontend is not connected to the worker.
- The worker and Docker image have not yet been built and run against an actual COLMAP installation in this environment.
- No real vehicle photograph set has been reconstructed yet.
- A COLMAP sparse model or dense PLY mesh is not yet a segmented, editable vehicle.
- No GLB export, part segmentation, component pivots, material editing or browser 3D editor integration exists yet.
- Customer authentication, multi-tenant authorization, encrypted remote storage, retention and malware scanning are required before accepting customer uploads.

## Engineering direction
- React, TypeScript and Vite web application.
- Three.js-based 3D editor integration in a later milestone.
- Local open-source photogrammetry, with no paid hosted vehicle-reconstruction API.
- HackyTech-owned capture guidance, job orchestration, vehicle-specific processing, geometry cleanup, part segmentation, editing and asset management.

Vehicle reconstruction requires many overlapping photographs. Reflective paint, glass, low-texture panels, occlusion and unseen surfaces remain difficult and require dedicated geometry/material processing.
