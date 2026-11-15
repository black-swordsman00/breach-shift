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
| Combat | [weapon](../breach_shift/combat/weapon.py), [target](../breach_shift/combat/target.py) | Manage ammunition, cooldowns and damageable scene actors. |
| Enemies | [zombie](../breach_shift/enemies/zombie.py), [catalog](../breach_shift/enemies/catalog.py) | Enemy behaviors, stats and introduction order. |
| Player | [health](../breach_shift/player/health.py), [jump](../breach_shift/player/jump.py) | Rendering-independent player state. |
| Training | [session](../breach_shift/training/session.py) | Shooting accuracy, elapsed time and session completion. |
| World | [levels](../breach_shift/world/levels.py), [scene](../breach_shift/world/scene.py), [navigation](../breach_shift/world/navigation.py), [reality](../breach_shift/world/reality.py) | Load and validate map definitions, render blockouts, navigate active geometry and switch realities. |

`CampaignGame` still extends the shared `BreachShift` class. The shared class
contains the working training arena and its input/HUD implementation; this
reorganization keeps that behavior while giving each subsystem a clear home.
Further extraction can follow concrete feature needs.

## Data and assets

[Campaign JSON](../breach_shift/data/levels) ships inside the package.
The loader uses `importlib.resources`, so starting a launcher from another
directory does not change which maps it loads. Its optional directory argument
still supports custom level definitions and validation tests.

[Assets](../assets) holds character/environment concepts, references, future
models, animations, textures and audio. Development concepts do not become
runtime assets automatically. The blockout scene and collision shapes remain
the integration reference until real production models are imported.

## Development conventions

- Put game behavior in its owning package and keep entry points small.
- Keep JSON map definitions separate from presentation assets.
- Keep health, ammunition, campaign progress and other state independent of the UI where practical.
- Add future production assets to their designated folders and preserve actor roots/collision bounds.
- Keep generated caches, local environments and build output out of version control.
- Run [the test suite](../tests) after changing imports, geometry or game behavior.
