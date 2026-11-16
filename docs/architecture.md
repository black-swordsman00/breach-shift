# 2D architecture

The game is a side-view platformer. All gameplay positions are horizontal x and
vertical z in metres. Panda3D draws flat cards in a single y plane through an
orthographic lens. No runtime model, rig, lighting or network client is loaded.

| Module | Responsibility |
| --- | --- |
| [app](../breach_shift/app.py) | Validate command-line mode and sector |
| [physics](../breach_shift/platformer/physics.py) | Swept rectangle movement, roofs, ceilings, one-way platforms and shot segments |
| [levels](../breach_shift/platformer/levels.py) | Validate ten authored side-view maps and their rosters |
| [session](../breach_shift/platformer/session.py) | Player, infected behaviors, hitscan, projectiles, reloads, loot and objectives |
| [game](../breach_shift/platformer/game.py) | Window, fixed 120 Hz stepping, camera, input, audio and HUD |
| [sprites](../breach_shift/platformer/sprites.py) | PNG atlas cards and frame selection |
| [scenery](../breach_shift/platformer/scenery.py) | Original parallax backgrounds, interior facades and visible platforms/gates |
| [arsenal](../breach_shift/combat/arsenal.py), [weapon](../breach_shift/combat/weapon.py) | Independent weapon state and ammunition |
| [progress](../breach_shift/campaign/state.py), [director](../breach_shift/campaign/director.py), [reality](../breach_shift/world/reality.py) | Sector progression, waves and safe Shift cooldown |
| [health](../breach_shift/player/health.py), [statistics](../breach_shift/training/session.py) | Reused independent state |

Simulation has no Panda3D imports. The renderer consumes its state and clears
sound events after playback. Pause and focus loss freeze simulation, reloads
and waves and release held fire. Input edges remain pending until a simulation
tick, so high frame rates do not lose a jump or reload press.

Use `restart_sector` for game retry. Panda3D calls its own `restart` while
constructing ShowBase; overriding it causes initialization failure. Keep the
engine's window-event handler so resizing and close behavior remain intact.

Shared solids and the active reality gate define the physical map. Changing
reality first validates the complete player body in the destination. Characters
use swept horizontal and vertical movement; feet land on tops and heads stop
at solid undersides. Only descending bodies land on one-way platforms.

Every packaged module must be reachable from the launcher. The
[source audit](../tools/release/check_sources.py) checks that constraint, local
documentation links, private path leakage and unexpected process/network imports.
[Route tests](../tests/test_side_routes.py) prove each map's geometry and
objectives are reachable using controls, with enemies disabled. Combat and
[real-framebuffer tests](../tests/test_side_render.py) cover the remaining rules.

The [art workflow](./2d-art.md) restores known model data from local Git history
only for optional offline baking. Model sources, Blender bundles and the old
first-person implementation are retired from the working tree. Runtime package
data is limited to map JSON, sprite PNG, sound WAV and provenance markdown.