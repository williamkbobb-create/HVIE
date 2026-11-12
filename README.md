# HackyTech Vehicle Intelligence Engine (HVIE)

Standalone photo-to-3D vehicle capture and customization workspace.

## Product flow
1. Create a vehicle project.
2. Upload overlapping photographs of one stationary vehicle.
3. Review capture coverage and image quality.
4. Send the capture set to a private reconstruction worker.
5. Inspect the reconstructed asset in a browser 3D workspace.
6. Customize body paint, wheels, seats, interior trim, glass and supported components.

## Current milestone
The browser app provides guided capture intake and coverage review. The private worker foundation supports authenticated, local-only intake, strict image validation, duplicate detection and private job manifests. The frontend is not connected to the worker. The worker does not yet execute COLMAP or produce a 3D asset.

## Engineering direction
- React, TypeScript and Vite web application.
- Three.js-based 3D editor integration in a later milestone.
- Isolated Python reconstruction worker using locally installed open-source tools such as COLMAP.
- No paid hosted vehicle-reconstruction API.
- Private storage, authentication, job queue and tenant authorization must be implemented before accepting customer uploads.

Vehicle reconstruction requires many overlapping views. Reflective paint, glass, occlusion and unseen surfaces remain difficult and require dedicated geometry/material processing.
