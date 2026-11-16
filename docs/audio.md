# 2D sound

Eighteen original mono PCM effects ship with the game: four gunshots, reload
start/finish, empty, ammunition pickup, three growls, two hurt variations, two
death variations, attack, howl and roar. No audio downloads or account is used.

The [sound bank](../breach_shift/audio/bank.py) keeps a bounded pool of four
voices per clip. The 2D view supplies volume from horizontal distance and clamps
playback pitch. Nearby infected emit staggered growls; Howlers and the Warden
have their own cues. M mutes/unmutes. Pause and retry stop old voices.

Sources are [SfxSynth.cs](../tools/audio/SfxSynth.cs) and the
[PowerShell generator](../tools/audio/Generate-Sfx.ps1). The generated
[WAV files](../breach_shift/data/audio) remain game package data.

For a silent check through the real OpenAL decoder:

```powershell
$env:ALSOFT_DRIVERS='null'
$env:PYTHONPATH='.'
.\.venv\Scripts\python.exe tools/audio/check_playback.py
```

The tests validate PCM format, nonempty samples, bounded voice reuse, mute,
empty-trigger throttling and cleanup. The former 3D audio manager is removed.