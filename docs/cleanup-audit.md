# 2D migration and workspace cleanup

Audit date: **16 November 2026**. The requested target is a side-view 2D game.
The new renderer and simulation were verified before retired files were removed.

The measured removal pass deleted **6,287 files / 1,676,225,460 bytes (1.56 GiB)**
across 130 checked targets. This includes ignored tool bundles and temporary
files as well as versioned content. Two additional obsolete HDRI/gallery helpers
were removed during the subsequent import/reference review.

| Removed group | Reason |
| --- | --- |
| Workspace Blender distribution, about 892 MiB | Optional 2D baking uses the existing Python environment; no bundled Blender executable is needed |
| Blender scenes, duplicate GLB/BAM exports, HDRI and MakeHuman build inputs | Runtime now consumes PNG sprites; the optional baker reads data from the pinned local Git revision |
| Primitive builders, PBR setup, first-person controllers, 3D AI/navigation and viewmodels | Replaced by the active platformer modules |
| Old top-down map JSON and 3D fixtures/tests | Replaced by ten side-view maps, swept-body, route and framebuffer regressions |
| Concept paintings, obsolete previews/gallery, design placeholders and old workflow documents | No active 2D runtime or maintenance consumer |
| Old provider polling scripts, intermediate renders, logs and source duplicates | No active generation is authorized; Fal.ai remains unused |

Every recursive target was resolved inside the project, checked against protected
paths, and rejected if it contained reparse points. No external download or user
application directory was removed. Git history and the active environment were
preserved. The former model sources remain recoverable from history.

A final check could not find the original supplied Warden at its previously
specified external location. One private raw source copy is therefore retained
in ignored storage. It is not packaged or pushed; deleting it without confirming
another original would be data loss. Credentials and Blender add-on settings
outside the project were not read or modified.

The remaining project's functions are documented in [architecture](./architecture.md),
[2D art](./2d-art.md), [combat](./combat.md) and [audio](./audio.md).
The [source audit](../tools/release/check_sources.py) rejects orphan runtime
modules, broken local documentation links, private local identifiers and
unexpected runtime network/process imports. The
[wheel check](../tools/release/check_wheel.py) requires the 2D assets and rejects
retired 3D content or extra runtime dependencies.

Automated route tests disable combat to prove physical reachability without
teleportation. Combat has separate tests. A manual full campaign and difficulty
review remain useful; automated verification is not a claim that balance is final.