# Breach Shift

An offline Python/Panda3D first-person zombie campaign built around switching
between Normal and Breach reality. The campaign uses placeholder geometry until
replacement map and character assets are supplied.

Run the campaign from the repository directory:

```powershell
.\.venv\Scripts\python.exe campaign_game.py
```

The original three-target training arena remains available:

```powershell
.\.venv\Scripts\python.exe main.py
```

Controls: WASD to move, mouse to look, left click to shoot, R to reload, Space
to jump, release and press Space again for a double jump, Shift to change
reality, E to interact, T to retry the current campaign map, and Escape to exit.
After campaign completion, T starts a new campaign. Training T retains its
original full training reset.

On each map, switch to Breach to cross the first barrier and recover the power
core with E. Return to Normal to cross the second barrier, defeat every zombie,
and enter the exit with E. Cores supply 24 reserve rounds and heal up to 20 HP.
Each new map is a checkpoint with full health and the starting ammunition.
Shift has a two-second cooldown and rejects destinations occupied by solid
geometry. Switching preserves health, ammunition, and enemy damage. Enemies
move faster in Breach; use its shortcuts carefully.

Run automated tests with:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Map definitions live in [levels](./levels). Each consecutive level introduces
one new zombie kind in the order defined by [the catalog](./zombie_catalog.py).
The maps are playable blockouts with shared and reality-specific obstacles;
their JSON coordinates are a layout reference for later replacement assets.
No external services, generated artwork, or runtime network access are used.
