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

## Campaign roster

Each level guarantees its new enemy appears. Previously introduced enemies
return in mixed packs; no enemy appears before its introduction.

| Map | New enemy | Combat lesson |
| --- | --- | --- |
| 1. Quarantine Yard | Walker | Keep distance and learn Shift barriers. |
| 2. Service Tunnels | Runner | Maintain an escape lane against fast pursuers. |
| 3. Freight Depot | Brute | Break sight lines during the red charge windup. |
| 4. Drainage Works | Spitter | Sidestep visible acid projectiles and use cover. |
| 5. Rooftop Crossing | Leaper | Change direction during its red leap windup. |
| 6. Security Checkpoint | Armored | Breach bypasses its Normal damage reduction. |
| 7. Broadcast Station | Howler | Prioritize summoners; each can summon twice. |
| 8. Isolation Ward | Stalker | Breach reveals enemies cloaked at a distance. |
| 9. Bio-Recovery Wing | Regenerator | Breach stops healing between hits. |
| 10. Breach Core | Warden | Damage it in Breach and jump to dodge its telegraphed stomp. |

## Replacement asset handoff

The ten maps are distinct playable blockout layouts. Environment art, zombie
skins, and animations can be supplied separately. Preserve the logical actor
roots and collision extents when replacing the placeholder models.

The arena uses Z-up coordinates, with X from -10 to 10 and Y from -5 to 20.
Level JSON stores obstacle center X/Y, width, depth, and height; obstacle bases
are at Z=0. The camera is 1.7 units above the player's feet. The `core` and
`exit` coordinates mark interaction points, and `spawns` lists enemy positions.
Shared blocks are solid in both realities; Normal and Breach blocks are
enabled only in their matching reality. Keep both Shift routes navigable.

Automated checks cover combat, safe Shift destinations, navigation and spawn
clearance, core/exit gating, all ten transitions, death/retry, and the original
training and jump behavior. A physical keyboard/mouse playthrough and balance
review of all ten levels remain manual validation steps.
