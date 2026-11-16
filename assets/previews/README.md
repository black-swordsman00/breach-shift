# Actual engine previews

Open the [interactive local model gallery](./gallery.html) to inspect individual
Blender renders, compare actual HP/damage and listen to sound samples. Links open
the corresponding editable Blender sources. Rebuild it with
`python tools/art/build_gallery.py` after changing balance or designs.

The following group views are captured from Panda3D using the actual exported
Blender models. They show the current anatomical art pass. The gameplay capture places two existing Walkers in view and equips
the rifle for inspection; it does not change the shipped level definition.

- [Gameplay, weapon, HP bars and fortress scenery](./gameplay.png)
- [All ten zombie models](./zombie-roster.png)
- [All four weapon models](./weapons.png)

Regenerate with `python -m breach_shift.art.preview --mode game`, `--mode roster`
or `--mode weapons`, passing `--output` to choose the destination.

The [character portraits](./characters) and [weapon portraits](./weapons) are
rendered in Blender under studio lights; they are not gameplay screenshots.
Neither set is a claim of final photorealistic art matching the concept paintings.
