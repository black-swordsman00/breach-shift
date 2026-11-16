"""Bake Blender-exported Poly Haven cube faces into an offline simplepbr map."""
import argparse
from pathlib import Path

from panda3d.core import Filename, PfmFile, Texture
from simplepbr.envmap import EnvMap


def bake(source: Path, output: Path):
    cube = Texture("polyhaven-courtyard-reflections")
    cube.setupCubeMap(64, Texture.TFloat, Texture.FRgb16)
    for face in range(6):
        pixels = PfmFile()
        if not pixels.read(Filename.fromOsSpecific(str(source / f"courtyard_{face}.exr"))):
            raise ValueError(f"Missing HDRI cube face {face}")
        if not cube.load(pixels, face, 0):
            raise ValueError(f"Could not load HDRI cube face {face}")
    cube.generateRamMipmapImages()
    environment = EnvMap(cube, prefiltered_size=32, prefiltered_samples=16,
                         blocking_prepare=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    environment.write(Filename.fromOsSpecific(str(output)))
    print(f"{output.name}: baked Poly Haven lighting with embedded textures")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()
    bake(arguments.source, arguments.output)
