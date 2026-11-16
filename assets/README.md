# Art assets

| Folder | Contents |
| --- | --- |
| [concepts/characters](./concepts/characters) | Generated character-design proposals; original and revised versions stay separate. |
| [concepts/environments](./concepts/environments) | Environment-design proposals for visual review. |
| [references/environments](./references/environments) | User-supplied environment inspiration. |
| [blender/characters](./blender/characters) | Ten editable character scenes with packed textures and review lighting. |
| [blender/weapons](./blender/weapons) | Four editable hard-surface weapon scenes with packed materials. |
| [blender/environments](./blender/environments) | Packed production courtyard scene with Poly Haven HDRI. |
| [models/environments](./models/environments) | Courtyard, switching barriers and reusable PBR architecture modules. |
| [models/props](./models/props) | Six normalized CC0 Poly Pizza props. |
| [models/weapons](./models/weapons) | Reviewed Rodin rifle GLB with measured muzzle metadata. |
| [models/characters](./models/characters) | Reviewed skinned Rodin Walker GLB and export metadata. |
| [designs/characters](./designs/characters) | Individual character proportions, colors and costume styles. |
| [Runtime characters](../breach_shift/data/models/characters) | Packaged runtime zombie models, including the female Runner. |
| [Runtime weapons](../breach_shift/data/models/weapons) | Packaged weapon models used by the first-person view. |
| [Runtime environments](../breach_shift/data/models/environments) | Self-contained production GLBs and matching map contract. |
| [Runtime audio](../breach_shift/data/audio) | Original weapon effects and positional zombie voices. |
| [previews](./previews) | Actual Panda3D screenshots for checking the current implementation. |

Characters are authored by [the Blender workshop tools](../tools/blender) and
installed with `python -m breach_shift.art.export` after GLB generation.
The game loads the compressed BAM.PZ files in a source
checkout and includes the same runtime models in the installable Python package.
Unused placeholder directories have been removed. PNG concept sheets remain
visual design references. See [the cleanup audit](../docs/asset-audit.md).
See [production credits](./LICENSE-PRODUCTION.md) and
[the production workflow](../docs/production-assets.md) for new assets.
The [Rodin model handoff](../docs/rodin-models.md) documents the first generated
rifle and Walker and their locally retained detailed sources.
See [the art brief](../docs/art-direction.md) and
[the map handoff](../docs/campaign.md#replacement-assets) before adding assets.
