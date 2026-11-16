# Anatomical source assets

The hm08 mesh and the `.target` morph data come from the official
[MakeHuman repository](https://github.com/makehumancommunity/makehuman/tree/a8bc2d54ff0ac92e78ff71431b1023eda42bf482),
revision `a8bc2d54ff0ac92e78ff71431b1023eda42bf482`.

These **asset files** explicitly carry a CC0 dedication. The full text is in
[LICENSE.ASSETS.md](./LICENSE.ASSETS.md). No MakeHuman application code is included.
The [project's license explanation](https://www.makehumancommunity.org/about/license.html)
distinguishes the application license from the CC0 core assets.

Upstream locations:

- `base.obj`: `makehuman/data/3dobjs/base.obj`
- Physique, sex and age targets: `makehuman/data/targets/macrodetails/`
- `mouth-open.target`: `makehuman/data/targets/expression/units/caucasian/mouth-open.target`

The Breach Shift Blender tools read this data directly, remove helper meshes,
convert the original Y-up coordinates to metre-based Z-up coordinates, and add
original clothing, painted decay, equipment, mutations and poses. Each resulting
character has a separate editable Blender scene and a runtime model. They are
adaptations of this anatomical base, not claims of entirely hand-sculpted anatomy.
