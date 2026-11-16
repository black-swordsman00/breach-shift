# Production courtyard asset credits

All downloaded sources listed below are **CC0 1.0**. The architecture meshes are
original Breach Shift work. No AI generation credits were used for architecture,
textures, lighting or props.

## Poly Haven PBR materials and lighting

| Source | Author(s) | Real-world repeat |
| --- | --- | --- |
| [Asphalt 02](https://polyhaven.com/a/asphalt_02) | Rob Tuytel | 3 m |
| [Concrete Wall 008](https://polyhaven.com/a/concrete_wall_008) | Charlotte Baglioni, Dario Barresi | 2.71 m |
| [Brick Wall 07](https://polyhaven.com/a/brick_wall_07) | Dimitrios Savva | 1.7 m |
| [Rusty Metal 03](https://polyhaven.com/a/rusty_metal_03) | Amal Kumar | 1.35 m |
| [Overcast Industrial Courtyard](https://polyhaven.com/a/overcast_industrial_courtyard) | Grzegorz Wronkowski | HDRI |

Material scans were acquired at 2K, then converted to 1K 8-bit game maps.
Diffuse, OpenGL tangent normals and roughness are embedded in the GLBs. The
Blender source packs the HDRI; the game uses a baked floating-point environment
map. See [Poly Haven's license](https://polyhaven.com/license).

## Poly Pizza set dressing

All six props below are by **Quaternius**, distributed through Poly Pizza:

| Model | Source triangles |
| --- | --- |
| [Barrier Large](https://poly.pizza/m/gLbBiYwt7l) | 624 |
| [Broken Car](https://poly.pizza/m/Y67erogmR9) | 5,432 |
| [Crate](https://poly.pizza/m/3VGWnZPXmG) | 784 |
| [Exploding Barrel](https://poly.pizza/m/1orHe0kCc1) | 516 |
| [Street Light](https://poly.pizza/m/nFwrlcLvM5) | 292 |
| [Debris Pile](https://poly.pizza/m/WrIiMMxyEP) | 424 |

Their geometry and material palette remain authored assets, normalized to metre
scale and arranged for the courtyard. The barrel is decorative; its source name
does not imply an explosion mechanic.

License text: [Creative Commons CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/legalcode).
The car is an environment prop; weapon and zombie triangle budgets do not apply
to it. Rodin is reserved for original weapons and characters and is not a source
for this courtyard.

## Supplied boss and retained character work

The [supplied Warden](./models/characters/warden.glb) has separate provenance
from the CC0 environment materials and props. It is a user-supplied PBR sculpt,
locally optimized and rigged without a new generation. No CC0 license is claimed
for this supplied model. The eight retained authored character designs keep
their MakeHuman/Breach Shift attribution and now use local skinned GLBs.
See [the Warden and motion handoff](../docs/warden-and-motion.md).
