# Production asset workflow

The first upgraded map is **Quarantine Yard**. The courtyard has 75,062 triangles
and 13 embedded textures, occupies about 25 MB, and uses metre units, Blender +Y
forward / +Z up. The GLB follows standard glTF Y-up encoding; `panda3d-gltf`
converts it back to Panda3D coordinates. Engine tests verify the resulting bounds.
The connected Blender 5.3 built this source scene; the retained earlier art
workshop was authored with Blender 4.5 LTS.

## Provider responsibilities

| Work | Provider / tool |
| --- | --- |
| Modular architecture, bevels, curbs, coping and structural trim | Blender |
| Asphalt, concrete, brick, rusted metal, HDRI | Poly Haven |
| Barricades, wrecks, crates, barrels, lamps, debris | Poly Pizza |
| New unique characters and primary tactical weapons | Hyper3D Rodin |

See [source credits and CC0 licenses](../assets/LICENSE-PRODUCTION.md).
No procedural weapon or zombie substitutes are generated when a provider or
production model is unavailable.

## First map build

Use the active BlenderMCP scene. Clear default objects, then acquire these
sources through its provider commands:

- `download_polyhaven_asset`: texture IDs `asphalt_02`, `concrete_wall_008`,
  `brick_wall_07`, `rusty_metal_03`; 2K PNG; HDRI
  `overcast_industrial_courtyard`, 1K HDR.
- `download_polypizza_model`: IDs and source links are in the credits. Normalize
  largest dimensions to 2.4 m for the barricade, 4.2 m for the car, 1.05 m for
  crates, 1 m for barrels, 5 m for lamps and 1.5 m for debris.
- Execute [the courtyard build](../tools/blender/build_courtyard.py) through
  BlenderMCP. A rebuild can also use the committed, normalized prop GLBs. Open
  [the packed environment scene](../assets/blender/environments/quarantine_yard.blend)
  first so its Poly Haven materials and world are present.

The builder clears the previous build, bakes mesh transforms with
`transform_apply(location=True, rotation=True, scale=True)`, projects architecture
UVs at each material's measured repeat size, packs images, and exports:

- [Complete courtyard and four switching barriers](../assets/models/environments).
- [Five reusable architecture modules](../assets/models/environments/modules).
- [Six normalized Poly Pizza props](../assets/models/props).
- An editable packed scene, plus matching packaged GLBs and collision metadata.

Game textures use 1K 8-bit color/normal/roughness maps. This avoids distributing
the original scan PNGs at 16-bit depth, which made the initial GLB about 147 MiB.
The full HDRI remains packed in the authoring scene. Since glTF does not include
world lighting, bake its six floating-point cube faces separately:

```powershell
.venv/Scripts/python.exe tools/art/build_environment_light.py .cache/courtyard-hdri breach_shift/data/lighting/courtyard.env
```

Large props sit on existing loading platforms, with additional collider volumes
for the car roofs, crates, barrels and barricades. These are conservative box
colliders. Navigation, player grounding, hitscan and Shift use the same level
definition. Shallow debris remains decorative. The map's geometry contract must
match the loaded level before its GLB replaces the fallback scenery; custom map
definitions retain their own geometry.

## Existing Rodin asset handoff

Paid generation is disabled for the current iteration. Reuse the existing rifle
and Walker sources and the supplied Warden file; no new provider calls are
needed. See [the generated model handoff](./rodin-models.md) and
[the Warden/motion handoff](./warden-and-motion.md). The eight retained authored
characters now use optimized skinned GLBs; three weapons retain earlier art.

For a completed weapon result, use [the Rodin optimizer](../tools/blender/optimize_rodin.py):

```powershell
blender --background --factory-startup --python tools/blender/optimize_rodin.py -- --source .cache/rodin-result.glb --output assets/models/weapons --kind rifle --length 0.92
```

Decimate preserves UV layers and enforces **strictly fewer than 5,000 triangles**.
It packs PBR images and exports a candidate GLB and sanitized editable scene.
Review its orientation, grip position, muzzle alignment, textures and silhouette
before copying it into the packaged weapon folder. Keep the measured muzzle JSON
alongside the GLB. The runtime loader prefers a
validated GLB over the matching older BAM. Generated zombies require fewer than
12,000 triangles **and** the animation pivots/rig expected by the game before
installation. Use [the character optimizer](../tools/blender/optimize_rodin_character.py)
to preserve UVs, fit the character budget and bind a local humanoid skeleton.

## Offline loading and privacy checks

The game uses local packaged assets and performs no runtime downloads. GLB
validation rejects external resources, custom extras, private filesystem paths,
invalid buffer lengths and unsupported required extensions. Blender saves strip
MCP scene settings and embedded scripts; image paths and every packed-image
source path are relative. The HDRI also has a local visible-sky PNG, while the
floating-point environment map supplies offline PBR reflections.
Scene dependencies are saved separately and reopened with a clean factory
layout, excluding the user's workspace UI and file-browser history. The saved
file is also scanned after decompression.
Provider credentials are read only by the locally configured add-on. The MCP
connection uses loopback and does not require opening an internet-facing port.

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -q
.venv/Scripts/python.exe -m breach_shift.art.preview --mode game
blender --background --factory-startup --disable-autoexec --python-exit-code 1 assets/blender/environments/quarantine_yard.blend --python tools/release/check_blend.py
.venv/Scripts/python.exe -m pip wheel . --no-deps --wheel-dir .cache/wheels
.venv/Scripts/python.exe tools/release/check_wheel.py .cache/wheels/breach_shift-0.1.0-py3-none-any.whl
```

Inspect [actual gameplay](../assets/previews/gameplay.png) separately from
[the Blender environment render](../assets/previews/quarantine-yard-blender.png).
Industrial facades, shutters, coping, platform ribs and lane markings refine
the courtyard while retaining its playable collision footprints. The other nine
maps and three weapons retain their earlier art. The eight earlier character
designs are locally optimized and fully skinned; they are not new generations.
