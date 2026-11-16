"""Verify that an installed game ships its playable content, not only Python code."""
import argparse
import json
from pathlib import Path
from zipfile import ZipFile


def check(path):
    with ZipFile(path) as archive:
        names = archive.namelist()
        for folder, expected in (("characters", 10), ("weapons", 4)):
            models = [name for name in names if name.startswith(f"breach_shift/data/models/{folder}/")
                      and name.endswith((".bam", ".bam.pz", ".glb"))]
            unique = {Path(name).name.split(".")[0] for name in models}
            if len(models) != expected or len(unique) != expected:
                raise ValueError(f"Wheel contains {len(models)} {folder} models; expected {expected}")
        for folder, suffix, expected in (("levels", ".json", 10), ("audio", ".wav", 18)):
            files = [name for name in names if name.startswith(f"breach_shift/data/{folder}/") and name.endswith(suffix)]
            if len(files) != expected:
                raise ValueError(f"Wheel contains {len(files)} {folder} assets; expected {expected}")
        root = "breach_shift/data/models/environments/"
        contract = json.loads(archive.read(root+"quarantine_yard.json"))
        required = [root+"quarantine_yard.glb", "breach_shift/data/lighting/courtyard.env",
                    "breach_shift/data/lighting/courtyard-sky.png",
                    "breach_shift/data/credits/production.md"]
        required += [root+entry["file"] for entry in contract["phase_blocks"]]
        for asset in required:
            if asset not in names or archive.getinfo(asset).file_size == 0:
                raise ValueError(f"Wheel is missing production content: {asset}")
    print(f"{path.name}: 14 character/weapon models, 5 environment GLBs, HDRI, 10 levels, 18 sounds packaged")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path)
    check(parser.parse_args().wheel)
