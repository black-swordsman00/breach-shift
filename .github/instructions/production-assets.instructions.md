---
description: Maintain the BlenderMCP production pipeline without duplicate generation charges or unsafe asset handoffs.
applyTo: 'tools/blender/**/*.py,breach_shift/art/**/*.py'
---

Use [the production workflow](../../docs/production-assets.md) and the user's
current scope and spending limits. Keep credentials in the configured add-on;
record accepted job IDs privately and poll/reuse those jobs before considering
another paid submission. Fix UVs, orientation, topology and rigging locally.

Paid generation is currently disabled by the user. Reuse supplied GLBs and
existing local source assets unless the user explicitly authorizes it again.

Imported GLBs can split coincident vertices at UV/normal seams. Weld positions
before Decimate while retaining per-corner UV layers; otherwise hard surfaces
can break into disconnected patches. Preserve the original source and bake PBR
detail onto a game UV channel when reduction distorts texture mapping.

Enforce fewer than 5,000 weapon triangles and 12,000 zombie triangles. Keep +Y
forward, +Z up and metre scale. Preserve expected model names, animation joints
and measured weapon muzzle coordinates when replacing assets.

Use [the clean save helper](../../tools/blender/production.py) and its factory
finalizer. A full interactive Blender save can include local file-browser paths.
Validate packed scenes, embedded GLBs, skin deformation and installed package
loading before replacing working assets or publishing source files.

## Learnings

Export the active scene only and compare the saved GLB triangle count with the
intended mesh selection. `select_all` excludes hidden retained source meshes;
clear all objects in the dedicated build scene before another batch build.

Sanitize both `Image.filepath` and every `ImagePackedFile.filepath`. Packed HDRIs
can retain an original short Windows user-directory alias even after the image
path is made relative; inspect decompressed scene bytes as well as Blender RNA.
