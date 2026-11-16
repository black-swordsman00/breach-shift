# Side-view combat

The four original weapon slots retain independent magazines, reserve ammo,
cooldowns and reload durations. The pistol and shotgun fire once per click;
the SMG and rifle repeat while held. Switching weapons cancels an unfinished
reload without granting ammunition. Shotgun pellets share one spent shell and
one accuracy event. Bullets hit the nearest enemy or architecture surface.

| Weapon | Damage | Magazine / reserve | Interval | Reload |
| --- | --- | --- | --- | --- |
| Pistol | 25 | 12 / 36 | 0.25 s | 1.5 s |
| SMG | 14 | 30 / 90 | 0.09 s | 1.8 s |
| Rifle | 38 | 24 / 72 | 0.18 s | 2.1 s |
| Shotgun | 96 over six pellets | 6 / 18 | 0.9 s | 2.8 s |

| Sector | Infected | HP | Distinct behavior |
| --- | --- | --- | --- |
| 1 | Walker | 75 | Ground pursuit and melee |
| 2 | Runner | 100 | Faster pursuit and attacks |
| 3 | Brute | 150 | Slower heavy melee |
| 4 | Spitter | 180 | Holds distance and fires visible projectiles |
| 5 | Leaper | 220 | Lunges and crosses gaps |
| 6 | Armored | 270 | Receives 65% incoming damage |
| 7 | Howler | 320 | Temporarily boosts nearby infected speed |
| 8 | Stalker | 380 | Translucent in Normal |
| 9 | Regenerator | 450 | Heals 5 HP/s after four seconds without damage |
| 10 | Warden | 800 | Vulnerable in Breach; telegraphed, jump-avoidable stomp |

Pursuit uses 1.5 times catalog speed and gains a further 20% in Breach. Non-leapers
stop at cliffs, and infected jump low solid obstacles. Solid gates block both
movement and line of sight. Head-height hits gain a damage bonus. The player
has a brief damage grace period to prevent overlapping instant melee kills.

Killed infected drop one weapon-specific ammo bundle. Its colour indicates
weapon type. Waves begin after 30 active seconds, increase over time and respect
a 32-alive cap. Recovering the core stops reinforcements and heals up to 25 HP.

Double jumps reset only on landing. Crouching lowers the actual body to 1.05 m
and halves movement speed; standing requires 1.8 m clearance. High spit can
pass overhead while crouched, and low spit still hurts. The Warden's stomp is
avoided when the player's feet are sufficiently above its ground level.

The firing range freezes target AI and tracks accepted shots, hits, accuracy
and completion time. T starts a fresh run. Campaign extraction requires the
core, zero living infected and Normal reality. Retry resets only the current
sector; retry after completing sector ten starts a new campaign.