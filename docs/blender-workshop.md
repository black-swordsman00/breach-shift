# Blender model workshop

Blender 4.5 LTS is the authoring tool. The game runs exported models directly;
players do not need Blender, MakeHuman or network access.

New environments use [the BlenderMCP production workflow](./production-assets.md)
with Poly Haven and Poly Pizza. Rodin is reserved for future character and main
weapon replacements. The tools below reproduce the retained earlier art library.

## Editable sources and reproduction

- `assets/blender/characters/`: ten `.blend` character scenes with packed images.
- `assets/blender/weapons/`: four `.blend` weapon scenes with packed images.
- `assets/designs/characters/`: per-character proportions, colors and costume style.
- `tools/blender/`: construction scripts and original skin-paint/material tools.
- `assets/source/makehuman/`: licensed CC0 anatomy and morph data, with provenance.
- `.cache/blender-export/`: intermediate GLBs; intentionally excluded from Git.
- `breach_shift/data/models/`: compressed runtime models shipped in the game package.
- `assets/previews/characters/` and `assets/previews/weapons/`: actual Blender renders.

For the local portable installation, rebuild one model or the full roster:

```powershell
& '.tools/blender-4.5.16-windows-x64/blender.exe' --background --factory-startup --python tools/blender/build_characters.py -- --kind walker --render
& '.tools/blender-4.5.16-windows-x64/blender.exe' --background --factory-startup --python tools/blender/build_characters.py -- --kind all --render
& '.tools/blender-4.5.16-windows-x64/blender.exe' --background --factory-startup --python tools/blender/build_weapons.py -- --kind all --render
```

On another machine, substitute the path to an installed Blender 4.5 LTS executable.
Blender itself and its downloaded archive are excluded from the repository.
Rendering is optional. Files contain a studio camera and lighting for inspection.
Open a `.blend` file in Blender to edit geometry and materials directly; rebuilding
from the scripts intentionally replaces those authored files.

## Game export contract

Characters use metre units, Z-up and face +Y. A root named `HERO_Walker` (or the
corresponding enemy name) contains named `Walker_body`, `Walker_arm_left`,
`Walker_arm_right`, `Walker_leg_left` and `Walker_leg_right` pivots. Weapons use
`WEAPON_Pistol`, `WEAPON_Smg`, `WEAPON_Rifle` and `WEAPON_Shotgun`, with +Y forward.
Do not rename these roots/pivots when editing in Blender.

Export only the chosen root and its descendants as GLB. Packed images and
Principled BSDF base-color, roughness, metallic and tangent normal maps travel
with the model. The importer embeds texture data, validates scale and animation
pivots, and writes the full source file successfully before replacing live assets.

```powershell
.venv/Scripts/python.exe -m breach_shift.art.blender_import .cache/blender-export/characters --compress
.venv/Scripts/python.exe -m breach_shift.art.blender_import .cache/blender-export/weapons --compress
.venv/Scripts/python.exe -m breach_shift.art.preview --mode roster
.venv/Scripts/python.exe -m breach_shift.art.preview --mode weapons
```

`BAM.PZ` files retain embedded textures and are transparently decompressed by
Panda3D. The first Walker shrank from roughly 20 MB to 6 MB through this lossless
step. A source GLB is never needed at runtime. `--output <directory>` and the
preview's `--model-dir <directory>` allow checking a candidate before installation.

## Current art limits

These are the first anatomical Blender production sources, not photorealistic
copies of the concept paintings. They use articulated rigid limb pivots for the
current lightweight walk animation. Full skeletal locomotion, sculpted close-up
skin, cloth simulation and final environment art remain later refinements.
Compare actual Blender and game captures separately from the concept references.
