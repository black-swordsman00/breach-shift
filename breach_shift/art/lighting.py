"""Small original image-based lighting maps for readable PBR silhouettes."""
from functools import lru_cache
from math import sqrt
from pathlib import Path

from panda3d.core import PNMImage, Texture


@lru_cache(maxsize=3)
def environment_map(profile="night"):
    from simplepbr.envmap import EnvMap

    if profile == "courtyard":
        path = Path(__file__).resolve().parents[1] / "data/lighting/courtyard.env"
        return EnvMap.from_file_path(str(path))

    size = 32
    cube = Texture("breach-shift-" + profile + "-reflections")
    cube.setupCubeMap(size, Texture.TUnsignedByte, Texture.FRgb)
    studio = profile == "studio"
    for face in range(6):
        image = PNMImage(size, size, 3)
        for y in range(size):
            for x in range(size):
                u, v = 2 * (x + .5) / size - 1, 2 * (y + .5) / size - 1
                direction = ((1, -u, -v), (-1, u, -v), (u, 1, -v),
                             (-u, -1, -v), (u, -v, 1), (u, v, -1))[face]
                length = sqrt(sum(value * value for value in direction))
                dx, dy, dz = (value / length for value in direction)
                key = max(0, -.45 * dx - .60 * dy + .66 * dz) ** 10
                rim = max(0, .70 * dx + .45 * dy + .55 * dz) ** 12
                sky = .025 + max(0, dz) * (.20 if studio else .08)
                strength = 1.0 if studio else .48
                image.setXel(x, y, sky + key * strength,
                             sky * 1.06 + key * strength * .90 + rim * strength * .35,
                             sky * 1.23 + key * strength * .73 + rim * strength * .65)
        cube.load(image, face, 0)
    cube.generateRamMipmapImages()
    return EnvMap(cube, prefiltered_size=16, prefiltered_samples=8, blocking_prepare=True)
