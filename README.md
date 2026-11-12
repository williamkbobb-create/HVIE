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
This branch establishes the standalone web application and browser-only capture intake. It does not yet upload photos, run COLMAP, produce a GLB, segment vehicle parts, or provide a reconstructed vehicle viewer. The intake threshold is a basic guard, not a guarantee of successful photogrammetry.

## Engineering direction
- React, TypeScript and Vite web application.
- Three.js-based 3D editor integration in a later milestone.
- Isolated Python reconstruction worker using locally installed open-source tools such as COLMAP.
- No paid hosted vehicle-reconstruction API.
- Private storage, authentication, job queue and tenant authorization must be implemented before accepting customer uploads.

Vehicle reconstruction requires many overlapping views. Reflective paint, glass, occlusion and unseen surfaces remain difficult and require dedicated geometry/material processing.
