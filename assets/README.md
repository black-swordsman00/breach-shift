# Art assets

| Folder | Contents |
| --- | --- |
| [concepts/characters](./concepts/characters) | Generated character-design proposals; original and revised versions stay separate. |
| [concepts/environments](./concepts/environments) | Environment-design proposals for visual review. |
| [references/environments](./references/environments) | User-supplied environment inspiration. |
| [Runtime characters](../breach_shift/data/models/characters) | Packaged runtime zombie models, including the female Runner. |
| [Runtime weapons](../breach_shift/data/models/weapons) | Packaged weapon models used by the first-person view. |
| [Runtime environments](../breach_shift/data/models/environments) | Reserved for exported modular map meshes and props. |
| [animations](./animations) | Future exported character animation clips. |
| [textures](./textures) | Future production material maps and decals. |
| [Runtime audio](../breach_shift/data/audio) | Original weapon effects and positional zombie voices. |
| [previews](./previews) | Actual Panda3D screenshots for checking the current implementation. |

Models are generated from [their source builders](../breach_shift/art) with
`python -m breach_shift.art.export`. The game loads these BAM files in a source
checkout and includes the same runtime models in the installable Python package.
Empty animation and environment-model folders reserve space for later
production work. PNG concept sheets remain visual design references.
See [the art brief](../docs/art-direction.md) and
[the map handoff](../docs/campaign.md#replacement-assets) before adding assets.
