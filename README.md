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
The browser app provides guided capture intake and coverage review. The private Python worker now includes authenticated local-only photo intake, image validation, duplicate detection, private job manifests and a SQLite-backed queue control plane. Workers can claim jobs using expiring leases, heartbeat to renew a lease, report failures for bounded retries, and cancel queued or running jobs.

The frontend is not connected to the worker. No background worker process or COLMAP command is connected yet. No 3D asset is produced, and jobs cannot be marked complete until validated reconstruction artifacts exist.

## Engineering direction
- React, TypeScript and Vite web application.
- Three.js-based 3D editor integration in a later milestone.
- Isolated Python reconstruction worker using locally installed open-source tools such as COLMAP.
- No paid hosted vehicle-reconstruction API.
- Private storage, customer authentication, tenant authorization, retention and security controls are required before accepting customer uploads.

Vehicle reconstruction requires many overlapping views. Reflective paint, glass, occlusion and unseen surfaces remain difficult and require dedicated geometry/material processing.
