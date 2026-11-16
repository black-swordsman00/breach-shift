# Offline 2D art

The game draws PNG sprite cards, four texture tiles and original flat scenery.
It does not load models, skeletal rigs, PBR shaders or remote content.

The local conversion produces 11 character atlases, four weapon sprites and six
prop sprites. Each infected has eight frames each of walking, idle, attack and
death. The player additionally has reload, crouch and jump poses. The supplied
Warden is retained as a rendered side-view boss, not regenerated.

The [manifest](../breach_shift/data/sprites/manifest.json) records dimensions,
physical sprite frames, animation rows, PNG digests and the immutable source
revision. [Credits](../breach_shift/data/credits/sprites.md) distinguish CC0
material/prop sources from supplied and previously generated art.

## Rebuild

The optional [baker](../tools/art/bake_sprites.py) retrieves known model data
from local Git history at `d74159abc1ffb763524c9697d492d021a1d4f785`.
Retired model copies and Blender installation bundles are unnecessary in the
working tree. The historical revision must exist locally; there is no network
fallback. No historical Python scripts are executed.

The development environment already used for the 3D game has the optional
dependencies. A fresh art environment can use [requirements-art.txt](../requirements-art.txt).
Only the game dependency is needed for normal play and tests.

```powershell
.\.venv\Scripts\python.exe tools/art/bake_sprites.py
.\.venv\Scripts\python.exe tools/art/bake_sprites.py --only player warden
```

Baking happens in an offscreen Panda3D window with embedded source textures.
The tool writes runtime PNGs and temporary model data under an ignored cache.
It never calls Fal.ai, Rodin, an asset marketplace or an API-key provider.
After a complete bake and asset checks, its temporary cache may be deleted.

Mirrorable sprite cards are two-sided: a negative horizontal scale otherwise
culls enemies facing left. This is covered by an actual renderer regression.
The baker and game keep their own names for level retry; Panda3D's `restart`
method is reserved for internal engine initialization.
