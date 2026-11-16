"""Verify that an installed game ships its playable content, not only Python code."""
import argparse
from pathlib import Path
from zipfile import ZipFile


def check(path):
    with ZipFile(path) as archive:
        names = archive.namelist()
        for folder, expected in (("characters", 10), ("weapons", 4)):
            models = [name for name in names if name.startswith(f"breach_shift/data/models/{folder}/")
                      and name.endswith((".bam", ".bam.pz"))]
            if len(models) != expected:
                raise ValueError(f"Wheel contains {len(models)} {folder} models; expected {expected}")
        for folder, suffix, expected in (("levels", ".json", 10), ("audio", ".wav", 18)):
            files = [name for name in names if name.startswith(f"breach_shift/data/{folder}/") and name.endswith(suffix)]
            if len(files) != expected:
                raise ValueError(f"Wheel contains {len(files)} {folder} assets; expected {expected}")
    print(f"{path.name}: 14 models, 10 levels, 18 sounds packaged")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path)
    check(parser.parse_args().wheel)
