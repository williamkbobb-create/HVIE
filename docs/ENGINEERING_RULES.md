# HVIE engineering rules

These rules are part of the project handover and apply to human developers and AI agents.

## Repository and branch boundaries

- Work only in `williamkbobb-create/HVIE`.
- Current approved working branch: `feature/standalone-app-foundation`.
- Do not change `main`, merge branches or create a production release without explicit approval.
- Do not modify the original Lavage Tracker repository or unrelated HackyTech, Grey, Oyosky or LogicalSky projects.
- Inspect the current tree and relevant source before editing.
- Preserve working features. Avoid broad rewrites when a focused change is sufficient.

## Cost and infrastructure

- Do not create paid resources, paid GPU instances, paid APIs, subscriptions or chargeable infrastructure without explicit approval.
- Prefer local and open-source development for the initial milestones.
- Explain likely compute, storage and hosting costs before proposing a paid route.
- Render static preview is not a reconstruction worker.

## Privacy and security

- Treat vehicle photos and generated assets as private project data.
- Never commit secrets, tokens, customer images, private storage or generated job artifacts.
- Keep the API local/loopback-bound during development.
- Do not accept real customer uploads until authentication, tenant isolation, encrypted storage, retention/deletion, malware scanning and abuse protections are implemented and reviewed.
- Use non-customer test data for early experiments.

## Technical honesty

- Distinguish code present from code executed.
- Distinguish fake/mock tests from actual COLMAP runs.
- Distinguish sparse points from dense geometry.
- Distinguish a PLY file from a quality-approved mesh.
- Distinguish a fused mesh from an editable vehicle with segmented parts.
- Distinguish a Three.js dependency from a working 3D editor.
- Never call the product complete or production-ready without end-to-end evidence.

## Change workflow

1. Inspect relevant files, branch and latest commit.
2. State the proposed scope and affected files.
3. Make the smallest coherent change.
4. Run relevant tests/builds where available.
5. Report exact commands, results and any tests not run.
6. Update project documentation and status evidence.
7. Ask before merging, production deployment or paid changes.

## AI handover protocol

A new AI must read the root README, this file, project handover, architecture and development status. Then it must inspect the live repository and latest CI runs. It should not trust an old chat summary as current state. If the AI cannot access the repository or execute tests, it must say so and request evidence rather than claiming success.
