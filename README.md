# Breach Shift

An offline Python/Panda3D first-person zombie campaign built around switching
between **Normal** and **Breach** reality. Ten playable maps introduce ten enemy
types. The game includes ten articulated procedural zombie models, four visible
weapon models, ammunition pickups and escalating reinforcements. Levels use
textured prototype geometry; the first courtyard includes snowy stone cover and
fortress towers. [Concept art](./assets/concepts) remains the target for later art refinement.

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

Enemies pursue the player directly over clear ground, route around cover, and
approach the nearest reachable side of a sealed barrier while waiting for Shift.

## Validation

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tests cover combat, collisions, navigation, safe Shift destinations, objectives,
all ten campaign transitions, retry, and training/jump behavior. A physical
keyboard/mouse playthrough and balance review remain manual checks.

Rebuild all fourteen exported runtime models, or capture the real renderer:

```powershell
.\.venv\Scripts\python.exe -m breach_shift.art.export
.\.venv\Scripts\python.exe -m breach_shift.art.preview --mode game
```

[Actual engine previews](./assets/previews/README.md) show the current game and models.

Gameplay runs offline and uses no external services or runtime network access.
Generated concept images are design references. Runtime models are reproducible
Panda3D meshes; this is an initial procedural art pass rather than the finished
high-detail appearance of the concept paintings.
