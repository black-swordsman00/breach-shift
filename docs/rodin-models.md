# First generated character and weapon

The rifle and Walker are generated with **Hyper3D Rodin v2.5 through fal.ai**.
Each has one accepted generation; all subsequent repairs, texture baking,
optimization, orientation, rigging and captures are local Blender/Panda3D work.
No account identifiers, request URLs or credentials are included in these assets.

| Asset | Source triangles | Game triangles | Runtime form |
| --- | --- | --- | --- |
| [Tactical rifle](../assets/models/weapons/rifle.glb) | 500,000 | 4,800 | Embedded PBR GLB, 0.92 m long |
| [Walker](../assets/models/characters/walker.glb) | 500,000 | 11,800 | Embedded PBR GLB, 1.8 m tall, skinned humanoid |

The [rifle source](../assets/blender/weapons/rifle.blend) and
[Walker source](../assets/blender/characters/walker.blend) retain hidden detailed
source meshes and their original UVs for future refinements without another
generation. The visible game meshes satisfy the strict budgets. Both sources
use a clean factory layout and packed, relative textures.

Imported glTF may split vertices at normal/UV seams. The optimizer welds matching
positions while retaining per-corner UVs before Decimate. The rifle also keeps
its source UV layer and adds a game UV channel; albedo, roughness, metallic and
tangent normals are baked locally from the detailed source. The Walker keeps
its generated UVs and receives a locally built skeleton with normalized weights.

Panda3D wraps the Walker as an independent Actor with the four joint controllers
used by the existing walk animation. Cleanup releases each actor's part bundles.
The rifle's measured muzzle comes from its packaged metadata. The first-person
view keeps depth testing in a near depth slice, so its surfaces occlude correctly
while nearby world walls do not hide the weapon.

The mixed-library export command prefers reviewed production GLBs and does not
recreate superseded BAM aliases. Earlier Blender builders skip migrated kinds
to protect reviewed editable sources. The supplied Warden replaces the old
boss, and eight earlier character designs now use locally optimized skinned
GLBs. Three weapons retain the earlier art. No additional generation was used
for the Warden/motion iteration; see [its handoff](./warden-and-motion.md).

Generated-model provider references are [Rodin on fal.ai](https://fal.ai/models/fal-ai/hyper3d/rodin/v2.5/text-to-3d)
and [Hyper3D](https://hyper3d.ai/). The courtyard's CC0 credits apply to its Poly
Haven and Poly Pizza sources; these generated models have separate provenance.

For the public renders, see [the model gallery](../assets/previews/gallery.html)
and [actual gameplay](../assets/previews/gameplay.png). Tests cover strict budgets,
source/runtime equality, physical scale, muzzle alignment, live vertex skinning,
independent skeleton instances, cleanup and rendered weapon occlusion.
