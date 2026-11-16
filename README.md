# Breach Shift

An offline Python/Panda3D first-person zombie campaign built around switching
between **Normal** and **Breach** reality. Ten playable maps introduce ten enemy
types. The game includes ten articulated Blender zombie models, four visible
weapon models, ammunition pickups and escalating reinforcements. Levels use
an upgraded first courtyard with Poly Haven PBR architecture and Poly Pizza
set dressing; the remaining maps retain prototype scenery.
The supplied Warden sculpt is the final boss. All ten zombies now have skinned
humanoid rigs, a distance-driven gait, attack poses and a short death animation.
[Concept art](./assets/concepts) remains the target for later art refinement.

## Run the game

Requires Python 3.10 or newer. Set up the local environment once:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Start the campaign from the project directory:

```powershell
.\.venv\Scripts\python.exe main.py
```

To practice against the Warden on the final map:

```powershell
.\.venv\Scripts\python.exe main.py --level 10
```

Start the original three-target training arena:

```powershell
.\.venv\Scripts\python.exe main.py --training
```

The equivalent module commands are `python -m breach_shift` and
`python -m breach_shift --training`, using the same environment. Run
`python main.py --help` for available options. The former standalone campaign
entry point is now the default mode of the single launcher.

For an editable package installation, `python -m pip install -e .` also provides
the `breach-shift` command. Campaign JSON is included as package data.

## Project layout

```text
Breach Shift/
├── main.py                 # Single source-checkout launcher
├── breach_shift/           # Importable game package
│   ├── app.py              # Game-mode selection
│   ├── art/                # Reproducible 3D meshes, export, viewmodels, previews
│   ├── core/               # Shared Panda3D game, controls, collisions, HUD
│   ├── campaign/           # Campaign loop, objectives, checkpoints
│   ├── combat/             # Weapons, ammunition, damageable targets
│   ├── enemies/            # Zombie catalog and AI
│   ├── player/             # Health, jump and double-jump state
│   ├── training/           # Training-session statistics
│   ├── world/              # Level loading, scene geometry, navigation, Shift
│   └── data/levels/        # Ten campaign map definitions
├── assets/                 # Concepts, references and production-art locations
├── docs/                   # Architecture, campaign and visual direction
├── tests/                  # Unit and Panda3D integration tests
├── pyproject.toml          # Package metadata, dependency and installed launcher
└── requirements.txt        # Dependency for running directly from this checkout
```

See [architecture](./docs/architecture.md) for module responsibilities,
[campaign design](./docs/campaign.md) for maps and gameplay, and
[art direction](./docs/art-direction.md) for the character and environment brief.
See [combat balance](./docs/combat.md) for HP, weapons, loot and reinforcement rules.

## Controls

| Input | Action |
| --- | --- |
| WASD / mouse | Move / look |
| Left click / R | Shoot / reload |
| 1 / 2 / 3 / 4 | Pistol / SMG / rifle / shotgun in the campaign |
| Space | Jump; release and press again for a double jump |
| C / Ctrl, held | Crouch with a lower camera/collider and slower movement |
| F1 | Show/hide the campaign controls panel |
| Shift | Change reality, with a two-second cooldown |
| E | Collect the power core or enter an unlocked exit |
| T | Retry the current map; restart after completing the campaign |
| Escape | Exit |
| M | Toggle sound |

In training, T resets the full practice session. On campaign maps, recover the
core in Breach, defeat every zombie, and return to Normal to reach the exit.
Hold left click for automatic fire with the SMG or rifle. Each weapon keeps
its own ammunition; changing weapons cancels an unfinished reload.

Each killed zombie drops a random weapon-specific ammunition box. Walk close
to collect it. Reinforcements begin after 30 active seconds and grow larger and
more frequent. Recovering the core seals reinforcements so the remaining
enemies can be cleared and the exit reached.

Weapons have distinct firing sounds plus reload and empty-magazine effects.
Zombies growl, react to hits and death, and announce attacks; their voices are
positioned in 3D and become quieter with distance. See [audio](./docs/audio.md).
Reloads animate the weapon and support hand using each weapon's real reload
duration. Movement, breathing, recoil and drawing blend into the first-person
pose. Cancelling or switching weapons clears the reload pose and pending ammo.

Enemies pursue the player directly over clear ground, route around cover, and
approach the nearest reachable side of a sealed barrier while waiting for Shift.

## Validation

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tests cover combat, collisions, navigation, safe Shift destinations, objectives,
all ten campaign transitions, retry, and training/jump behavior. A physical
keyboard/mouse playthrough and balance review remain manual checks.

After building the Blender source library, install its fourteen runtime models
or capture the real renderer:

```powershell
.\.venv\Scripts\python.exe -m breach_shift.art.export
.\.venv\Scripts\python.exe -m breach_shift.art.preview --mode game
```

[Actual engine previews](./assets/previews/README.md) show the current game and models.
The [local review gallery](./assets/previews/gallery.html) includes Blender
portraits, statistics, sounds and editable source links.
See [the Blender workflow](./docs/blender-workshop.md) to edit or rebuild them.

See [the production asset workflow](./docs/production-assets.md) for the first
modular courtyard, licenses, GLB export checks and the Rodin weapon handoff.
The first [Rodin rifle and skinned Walker](./docs/rodin-models.md) now run in-game;
their detailed sources are retained for local refinement.

Gameplay runs offline and uses no external services or runtime network access.
See the [ZombieModding source review](./docs/map-source-review.md) before
selecting downloadable replacement maps. No third-party map installers are
part of the game or its asset workflow.
Generated concept images are design references. Retained character sources use
licensed CC0 anatomy and original costumes, painted decay, equipment and mutations.
The Rodin rifle and Walker have generated geometry with local Blender optimization;
the Walker uses a skinned skeleton. Editable sources retain their detailed meshes.
Runtime BAM.PZ and GLB models embed textures and ship in the installed package,
alongside the environment's baked Poly Haven HDRI. The concept paintings remain
the visual target; authored locomotion clips and further environment art are
future work.
