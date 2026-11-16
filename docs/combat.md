# Combat balance and encounter rules

## Zombie health

HP is unique for every enemy and increases in introduction order. Existing
armor, cloaking, regeneration and Breach rules still apply.

| Map | Enemy | HP | Melee/projectile damage |
| --- | --- | --- | --- |
| 1 | Walker | 75 | 12 |
| 2 | Runner, adult female model | 100 | 8 |
| 3 | Brute | 150 | 28 |
| 4 | Spitter | 180 | 10 |
| 5 | Leaper | 220 | 18 |
| 6 | Armored | 270 | 16 |
| 7 | Howler | 320 | 11 |
| 8 | Stalker | 380 | 14 |
| 9 | Regenerator | 450 | 15 |
| 10 | Warden | 800 | 35 |

Nearby enemies have a name and HP bar. A cloaked Stalker also hides its HP
display. Walking limbs, hit flashes and attack warnings use independent model
instances, so animating one enemy does not move another.
Pursuit movement is 20% faster than the original catalog speed, with the
existing additional 35% Breach multiplier. The supplied Warden is 2.6 m tall
with a wider collider and navigation clearance. Its 800 HP and 35-damage stomp
remain the strongest enemy profile. Footstep cycles follow actual distance;
knees, elbows, hips, spine and head blend their motion independently. Death
removes collision immediately and leaves a briefly falling visible body.

## Weapons

All four slots are available in the campaign. Training keeps its original pistol.

| Key | Weapon | Damage | Magazine / initial reserve | Fire interval | Reload | Range |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Pistol | 25 | 12 / 36 | 0.25 s | 1.5 s | 100 m |
| 2 | SMG | 14 | 30 / 90 | 0.09 s, automatic | 1.8 s | 65 m |
| 3 | Rifle | 38 | 24 / 72 | 0.18 s, automatic | 2.1 s | 160 m |
| 4 | Shotgun | Up to 96 | 6 / 18 | 0.9 s | 2.8 s | 24 m |

The shotgun traces six spreading pellets at 16 damage each, spending one shell.
Walls block each pellet independently. All weapons have a distinct visible
model, gloved player arms, recoil and a short muzzle flash. Switching slots
preserves ammunition and fire cooldown and cancels an unfinished reload.
The support hand and weapon animate a reload for its exact gameplay duration;
the HUD shows progress. Ammunition is granted only when the reload completes.
Each map checkpoint refills every weapon and retains the selected slot.

## Ammunition drops

Every enemy killed through the combat system creates exactly one random
weapon-specific pickup. The four weapon types have equal selection probability;
the amount is uniformly selected within the bundle range below.

| Ammunition | Rounds per box |
| --- | --- |
| Pistol | 6–18 |
| SMG | 15–40 |
| Rifle | 10–25 |
| Shotgun | 2–6 shells |

Walk within 1.5 m to collect. A wall or excessive height difference blocks
collection. Ammo is added to its matching weapon even if another is equipped.
Pickups last 90 active seconds, with a maximum of 64 on the map. Retry and map
transitions clear old pickups; dead enemy scene nodes are pruned after 10 seconds.

## Timed reinforcements

The first wave is due at 30 seconds of active play. Wave size is
`min(2 + floor(active_seconds / 30), 10)`, also limited by the free places under
the 32-enemy alive cap. After each wave the next interval is
`max(8, 26 - 2 * wave_number)` seconds. A delayed update never spawns several
catch-up waves in a single frame.

Spawns are at least 12 m from the player, on ground safe in both realities,
in the player's current reachable navigation component, away from living
enemies. Only already introduced enemy types are selected. Timed waves do not
create additional Wardens. Losing window focus, dying or completing the
campaign stops active encounter time. Retrying or entering a new map resets it.

Recovering the power core seals timed reinforcements for the current map.
This preserves a finite clear-and-exit objective. Existing Howler summons
remain bounded by their per-enemy budget and the shared alive cap.
