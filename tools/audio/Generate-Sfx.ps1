$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$outputDirectory = Join-Path $projectRoot 'breach_shift\data\audio'
New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
Add-Type -Path (Join-Path $PSScriptRoot 'SfxSynth.cs')
$cues = @('pistol', 'smg', 'rifle', 'shotgun', 'reload_start', 'reload_finish', 'empty', 'ammo_pickup',
          'growl_1', 'growl_2', 'growl_3', 'hurt_1', 'hurt_2', 'death_1', 'death_2', 'attack', 'howl', 'roar')
foreach ($cue in $cues) {
    $audioBytes = [BreachShiftSfx]::Render($cue)
    $outputPath = Join-Path $outputDirectory ($cue + '.wav')
    [IO.File]::WriteAllBytes($outputPath, $audioBytes)
    Write-Output ($cue + ': ' + $audioBytes.Length + ' bytes')
}
