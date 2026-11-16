---
description: Maintain the offline side-view game and its small, auditable sprite package.
applyTo: 'breach_shift/**/*.py,tools/art/**/*.py,tools/release/**/*.py'
---

The active game is a 2D side-view platformer. Use flat PNG cards with an
orthographic camera. Gameplay positions are horizontal x and vertical z;
the renderer's y is only a layer plane. Keep simulation independent of Panda3D.

Every packaged module and asset needs a current consumer. Run the source audit,
tests and wheel check after removing files. Retired 3D code, models, Blender
bundles and placeholder galleries should not return to the runtime package.

Paid generation remains disabled. Reuse supplied/existing work. The optional
sprite baker reads data from a pinned local Git revision; it must not execute
historical scripts, download tools or call provider services. Retain the private
original source in ignored storage until another original copy is confirmed.

Mirrorable sprite cards must be two-sided. Test actual framebuffer visibility
for a left-facing enemy; checking only the scene graph misses backface culling.
Use a distinct name such as `restart_sector` for retry: `ShowBase.restart`
is called during Panda3D initialization. Preserve default window-event handling.

Run movement at a fixed 120 Hz. Use full body rectangles, ceiling clearance,
and swept landing tests. Add route tests for all maps using real movement and
Shift controls; teleport-only objective tests do not prove map reachability.

Pause and window focus loss must freeze simulation, reloads and waves, clear
held fire and show the native cursor. Never inspect keys, open ports, disable
system protection or include private file paths in public assets/metadata.

Privacy scans must distinguish absolute private paths from generic CI account
names. For example, GitHub's `runner` username is also a valid infected type;
matching that bare word as a secret breaks every Linux build.
