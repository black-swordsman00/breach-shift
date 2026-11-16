# Audio and pursuit

The game bundles eighteen original mono PCM effects. No recording downloads,
audio service or account is needed at runtime. Four effects distinguish the
pistol, SMG, rifle and shotgun. Further clips cover reload start/finish, dry
fire, ammunition pickup, three growls, two hurt/death variations, attack,
Howler call and Warden roar.

Weapon sounds follow successful shots and reload events. Enemy sounds use
Panda3D's OpenAL 3D manager, with the player camera as listener and the enemy
as source. Attenuation begins at 3 m, with a 45 m falloff range. Idle vocal
events are emitted only within 40 m and are staggered between enemies.
Small reusable voice pools bound memory and permit overlapping sounds.
Press M to mute/unmute; map changes stop and detach old enemy voices.

Sources live in [the sound generator](../tools/audio/SfxSynth.cs), with a
[PowerShell build helper](../tools/audio/Generate-Sfx.ps1). Generated WAV files
ship in [package data](../breach_shift/data/audio). Windows filenames are
converted to Panda3D's virtual filesystem notation before loading.

For a silent real-backend decode and positional-audio check:

```powershell
$env:ALSOFT_DRIVERS = 'null'
.\.venv\Scripts\python.exe -m tools.audio.check_playback
```

The process-level null-driver setting belongs to this check, not normal gameplay.
The [automated tests](../tests/test_audio.py) validate every bundled WAV, voice
pool reuse, distance settings, dry-fire debouncing and mute/cleanup behavior.

## Pursuit correction

Replanning previously started at the nearest rounded cell, which could repeatedly
pull a slow enemy back toward the same point. Movement now follows a direct
clear segment or a route that omits that stale starting waypoint. A swept
clearance check prevents passing through cover or a thin gate between frames.

When a closed reality barrier separates the player and an enemy, the enemy
approaches the closest reachable point rather than idling at its distant spawn.
The barrier remains solid. Ranged attack distances, melee cooldowns, jumping
avoidance and reality-specific rules remain in place.
