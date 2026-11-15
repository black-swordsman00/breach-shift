# Art assets

| Folder | Contents |
| --- | --- |
| [concepts/characters](./concepts/characters) | Generated character-design proposals; original and revised versions stay separate. |
| [concepts/environments](./concepts/environments) | Environment-design proposals for visual review. |
| [references/environments](./references/environments) | User-supplied environment inspiration. |
| [models/characters](./models/characters) | Ten exported BAM zombie models, including the female Runner. |
| [models/weapons](./models/weapons) | Four exported BAM weapon models used by the first-person view. |
| [models/environments](./models/environments) | Future modular map meshes and props. |
| [animations](./animations) | Future exported character animation clips. |
| [textures](./textures) | Future production material maps and decals. |
| [audio](./audio) | Future sound effects, ambience and music. |
| [previews](./previews) | Actual Panda3D screenshots for checking the current implementation. |

Models are generated from [their source builders](../breach_shift/art) with
`python -m breach_shift.art.export`. The game loads these BAM files in a source
checkout and falls back to the same builders when packaged without local art.
Empty animation, environment-model and audio folders reserve space for later
production work. PNG concept sheets remain visual design references.
See [the art brief](../docs/art-direction.md) and
[the map handoff](../docs/campaign.md#replacement-assets) before adding assets.
