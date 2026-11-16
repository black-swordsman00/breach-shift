# Supplied Warden and local motion pass

The user-supplied PBR GLB replaces the Warden on map 10. It was imported through
the active local BlenderMCP connection and inspected with
`get_viewport_screenshot`. No fal.ai generation, retry or paid add-on was used.

| Measurement | Supplied mesh | Game mesh |
| --- | --- | --- |
| Triangles | 500,000 | 11,800 |
| Dimensions (X / Y / Z) | 1.366 / 0.928 / 1.893 m | 1.876 / 1.281 / 2.600 m |
| Forward / up | -Y / +Z | +Y / +Z |
| PBR maps | Three embedded 2K maps | Three embedded 2K maps |
| Skeleton | None | 17 bones, normalized four-weight skin |

The [game GLB](../assets/models/characters/warden.glb) and
[packed editable source](../assets/blender/characters/warden.blend) retain UVs
and a hidden detailed source. The [viewport inspection](../assets/previews/characters/warden-viewport.png)
shows the reimported optimized export. Transforms are applied, feet sit at Z=0,
and one unit is one metre. Standard glTF Y-up encoding is converted correctly
by `panda3d-gltf`.

Eight earlier MakeHuman/Breach Shift character designs also receive local
humanoid rigs and UV-preserving decimation: 11,798-11,800 triangles each. The
existing generated Walker remains at 11,800. These are edits to retained assets,
with their original provenance preserved, rather than new AI generations.

Movement is driven by distance travelled, so blocked and idle enemies stop
cycling their legs. Turning, arm swing, knees, feet, hips, torso and breathing
blend together. Windups and strikes add combat poses; leapers tuck their legs
in the air. Corpses lose collision immediately, fall, and are cleaned up after
the existing ten-second lifetime. Boss routes use clearance for the wider body.

All four weapons have local reload hand/weapon motion aligned to the actual
reload timer, plus drawing, breathing, locomotion, look sway and recoil. Switching
slots or retrying clears the reload pose. The weapon shader retains proper
self-occlusion, and the HUD progress meter does not grant ammo early.

C / Ctrl holds crouch, lowers the eye and collision sphere, and reduces movement
speed. Standing waits for head clearance under low ceilings. Release, focus
loss and retry clear the held input. F1 displays controls. The campaign HUD has
separate health, objective, reality, ammunition and boss panels, with retry/end
feedback. Quarantine Yard also gains factory facades, trim, road markings,
dynamic shadows and a visible sky from its existing licensed HDRI.

```powershell
.\.venv\Scripts\python.exe main.py --level 10
```

[Animated Panda3D capture](../assets/previews/gameplay-motion.png) and
[reload/crouch sequence](../assets/previews/reload-crouch-sequence.png) show a
clearly labelled courtyard animation showcase with a Walker and Warden. The
regular [gameplay capture](../assets/previews/gameplay.png) shows the actual
first-map roster. Other nine environments and three weapon meshes remain the
earlier art; this pass improves their character motion and first-person handling.

Validation covers independent live skin deformation for every character,
embedded textures, strict budgets, bounds, pursuit clearance, crouch/projectile
interaction, reload timing/cancellation, weapon depth, all campaign transitions
and installed-package loading. Authoring scenes are checked in factory Blender
with auto-execution disabled; image and packed-image paths are relative and
decompressed scene bytes are scanned for private path prefixes.
