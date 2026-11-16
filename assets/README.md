# Art assets

| Folder | Contents |
| --- | --- |
| [concepts/characters](./concepts/characters) | Generated character-design proposals; original and revised versions stay separate. |
| [concepts/environments](./concepts/environments) | Environment-design proposals for visual review. |
| [references/environments](./references/environments) | User-supplied environment inspiration. |
| [blender/characters](./blender/characters) | Ten editable character scenes with packed textures and review lighting. |
| [blender/weapons](./blender/weapons) | Four editable hard-surface weapon scenes with packed materials. |
| [designs/characters](./designs/characters) | Individual character proportions, colors and costume styles. |
| [Runtime characters](../breach_shift/data/models/characters) | Packaged runtime zombie models, including the female Runner. |
| [Runtime weapons](../breach_shift/data/models/weapons) | Packaged weapon models used by the first-person view. |
| [Runtime environments](../breach_shift/data/models/environments) | Reserved for exported modular map meshes and props. |
| [animations](./animations) | Future exported character animation clips. |
| [textures](./textures) | Future production material maps and decals. |
| [Runtime audio](../breach_shift/data/audio) | Original weapon effects and positional zombie voices. |
| [previews](./previews) | Actual Panda3D screenshots for checking the current implementation. |

Characters are authored by [the Blender workshop tools](../tools/blender) and
installed with `python -m breach_shift.art.export` after GLB generation.
The game loads the compressed BAM.PZ files in a source
checkout and includes the same runtime models in the installable Python package.
Empty animation and environment-model folders reserve space for later
production work. PNG concept sheets remain visual design references.
See [the art brief](../docs/art-direction.md) and
[the map handoff](../docs/campaign.md#replacement-assets) before adding assets.
