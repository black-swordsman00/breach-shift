# Architecture

The project uses one importable `breach_shift` package and one source-checkout
launcher. Imports name the owning package explicitly; no module depends on
the current working directory or adds folders to `sys.path`.

## Responsibilities

| Area | Main modules | Responsibility |
| --- | --- | --- |
| Entry points | [launcher](../main.py), [app](../breach_shift/app.py), [module entry](../breach_shift/__main__.py) | Parse the mode and start its game loop. |
| Shared game | [core/game](../breach_shift/core/game.py) | Panda3D setup, first-person input, movement, collisions, shooting callbacks, HUD and the original training arena. |
| Campaign | [campaign/game](../breach_shift/campaign/game.py), [state](../breach_shift/campaign/state.py) | Extend the shared game with enemy encounters, objectives, progression and retry. |
| Reinforcements | [director](../breach_shift/campaign/director.py) | Advance waves using active gameplay time, enforce the alive cap and stop after core recovery. |
| Combat | [weapon](../breach_shift/combat/weapon.py), [target](../breach_shift/combat/target.py) | Manage ammunition, cooldowns and damageable scene actors. |
| Arsenal and loot | [catalog](../breach_shift/combat/catalog.py), [arsenal](../breach_shift/combat/arsenal.py), [loot](../breach_shift/combat/loot.py) | Describe four weapons, preserve their independent state and roll ammunition rewards. |
| Runtime art | [characters](../breach_shift/art/characters.py), [weapons](../breach_shift/art/weapons.py), [export](../breach_shift/art/export.py) | Build reproducible articulated 3D meshes, load exported BAM models and animate the first-person weapon. |
| Enemies | [zombie](../breach_shift/enemies/zombie.py), [catalog](../breach_shift/enemies/catalog.py) | Enemy behaviors, stats and introduction order. |
| Player | [health](../breach_shift/player/health.py), [jump](../breach_shift/player/jump.py) | Rendering-independent player state. |
| Training | [session](../breach_shift/training/session.py) | Shooting accuracy, elapsed time and session completion. |
| World | [levels](../breach_shift/world/levels.py), [scene](../breach_shift/world/scene.py), [navigation](../breach_shift/world/navigation.py), [reality](../breach_shift/world/reality.py) | Load and validate map definitions, render blockouts, navigate active geometry and switch realities. |

`CampaignGame` still extends the shared `BreachShift` class. The shared class
contains the working training arena and its input/HUD implementation; this
reorganization keeps that behavior while giving each subsystem a clear home.
Further extraction can follow concrete feature needs.

## Player movement against architecture

[The player body guard](../breach_shift/player/collision.py) sweeps a full
1.8-metre standing or 1.15-metre crouching body against active box colliders.
It stops feet at roofs, heads at ceilings and horizontal motion at side faces,
then permits sliding along walls. The old torso sphere alone could pass above
a crate while the player's legs entered its side. Roof support now considers
the player's footprint rather than only the centre ray.

Panda3D still handles boundary planes, moving enemies and the ground ray.
The body guard also constrains displacement caused by the pusher. Stashed
targets and inactive reality blocks are excluded through the active scene
graph. A ceiling impact stops ascent without resetting airborne jumps.

This guard uses world-aligned box bounds; rotated architecture is conservative.
It is not a general imported-mesh or stair controller. New environment assets
need matching collision geometry, and multilevel maps need navigation work.
Regression tests cover crate sides near roof height, edge support, ceilings,
fast movement and falls onto playable blocks on all ten maps in both realities.

## Data and assets

[Campaign JSON](../breach_shift/data/levels) ships inside the package.
The loader uses `importlib.resources`, so starting a launcher from another
directory does not change which maps it loads. Its optional directory argument
still supports custom level definitions and validation tests.

[Assets](../assets) holds character/environment concepts, references, future
models, animations, textures and audio. Exported character and weapon meshes
are loaded through [the model library](../breach_shift/art/library.py), with a
source-builder fallback for an installed package. The initial art pass uses
the existing logical actor roots and collision extents. Scene batching must
preserve those roots and the limb pivots; use `flatten_local` for positioned
anchors rather than baking their transforms away.

## Development conventions

- Put game behavior in its owning package and keep entry points small.
- Keep JSON map definitions separate from presentation assets.
- Keep health, ammunition, campaign progress and other state independent of the UI where practical.
- Add future production assets to their designated folders and preserve actor roots/collision bounds.
- Keep generated caches, local environments and build output out of version control.
- Run [the test suite](../tests) after changing imports, geometry or game behavior.
