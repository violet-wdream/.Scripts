#!/usr/bin/env python3

import shutil
from pathlib import Path

INPUT_PATH = r"D:\Tools\UsefulTools\MuMu\Shared\Download\resources\output\zh\spine"
DRYRUN = True


def atlas_pngs(atlas):
    with atlas.open(encoding="utf-8", errors="ignore") as f:
        return {
            line.strip()
            for line in f
            if line.strip().lower().endswith(".png")
            and ":" not in line
        }


def move(src, dst):
    # print(f"[{'DRYRUN' if DRYRUN else 'MOVE'}] {src.name} -> {dst.name}/")

    if not DRYRUN:
        dst.mkdir(parents=True, exist_ok=True)
        shutil.move(src, dst / src.name)
        
        
def main():
    root = Path(INPUT_PATH)

    for atlas in root.rglob("*.atlas"):
        png_names = atlas_pngs(atlas)
        target = root / atlas.stem

        # print(f"\n[ATLAS] {atlas.relative_to(root)}")

        move(atlas, target)

        for ext in (".skel", ".json"):
            file = root / f"{atlas.stem}{ext}"
            if file.exists():
                move(file, target)

        for name in png_names:
            matches = list(root.rglob(name))

            if not matches:
                print(f"[WARN] PNG 不存在: {name}")
            elif len(matches) > 1:
                print(f"[CONFLICT] PNG 重名: {name}")
            else:
                move(matches[0], target)
                
if "__main__" == __name__:
    main()