# Asset cleanup and production handoff

The cleanup keeps every campaign definition, gameplay module, test, audio effect,
fourteen shipped Blender models and their editable sources. The initial suite
passed all 155 tests before changes.

Removed obsolete content:

- Procedural zombie and weapon templates, the hidden missing-model fallback and
  the obsolete procedural-export command. A missing shipped model now reports an
  actionable error instead of displaying primitive art.
- Empty animation, audio, texture and environment placeholder markers. Actual
  audio remains in the packaged audio bank.
- Ignored study generators and candidate models, stale package builds and the
  redundant portable Blender download archive. The extracted Blender installation
  remains available. This reclaimed about 480 MiB locally.

Retained content has active consumers: primitive mesh utilities still build
gameplay markers, player arms, collision-aligned environment fallbacks and
effects; the anatomical Blender workshop and licensed MakeHuman sources still
reproduce the existing characters and have dedicated tests. Concepts and
previews remain visual references. These are not unused placeholders.

Production replacements use Poly Haven for architecture materials and HDRI,
Poly Pizza for licensed set dressing, and Hyper3D Rodin only for characters and
primary weapons. Existing working assets remain installed until replacements
pass geometry, embedded-texture and Panda3D loading checks.

BlenderMCP listens on loopback. Provider credentials stay in the local add-on;
they must not appear in scripts, saved scenes, GLB extras, manifests or commits.
The game remains offline and never downloads assets at runtime.
