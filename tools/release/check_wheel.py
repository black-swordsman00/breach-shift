"""Verify that an installed game ships its playable content, not only Python code."""
import argparse
import json
from pathlib import Path
from zipfile import ZipFile


def check(path):
    with ZipFile(path) as archive:
        names = archive.namelist()
        if any(name.endswith((".glb",".blend",".bam",".bam.pz",".env")) for name in names):
            raise ValueError("A retired 3D asset entered the 2D wheel.")
        for folder, suffix, expected in (("platforms", ".json", 10), ("audio", ".wav", 18)):
            files = [name for name in names if name.startswith(f"breach_shift/data/{folder}/") and name.endswith(suffix)]
            if len(files) != expected:
                raise ValueError(f"Wheel contains {len(files)} {folder} assets; expected {expected}")
        root = "breach_shift/data/sprites/"
        contract = json.loads(archive.read(root+"manifest.json"))
        expected = {"player","walker","runner","brute","spitter","leaper","armored","howler",
                    "stalker","regenerator","warden","pistol","smg","rifle","shotgun",
                    "barricade","car","crate","barrel","lamp","debris"}
        if set(contract["sprites"])!=expected:
            raise ValueError("Incomplete or unused sprite content in wheel.")
        required = [root+entry["file"] for entry in contract["sprites"].values()]
        required += [root+"tiles/"+name+".png" for name in ("asphalt","concrete","brick","metal")]
        required += ["breach_shift/data/credits/sprites.md"]
        for asset in required:
            if asset not in names or archive.getinfo(asset).file_size == 0:
                raise ValueError(f"Wheel is missing production content: {asset}")
        metadata_name = next(name for name in names if name.endswith(".dist-info/METADATA"))
        dependencies = [line for line in archive.read(metadata_name).decode().splitlines() if line.startswith("Requires-Dist:")]
        if len(dependencies)!=1 or "panda3d==1.10.16" not in dependencies[0]:
            raise ValueError("Unexpected 2D runtime dependencies.")
    print(f"{path.name}: 21 sprites, 4 tiles, 10 side-view maps and 18 sounds; Panda3D-only runtime")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path)
    check(parser.parse_args().wheel)
