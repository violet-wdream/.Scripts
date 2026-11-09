# cocos TexturePacker .plist -> Spine .atlas
import plistlib
import re
from pathlib import Path

_RECT_RE = re.compile(r"\{\{(-?\d+),(-?\d+)},\{(-?\d+),(-?\d+)}}")
_SIZE_RE = re.compile(r"\{(-?\d+),(-?\d+)}")


def _size(s):
    m = _SIZE_RE.search(s or "")
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)


def _rect(s):
    m = _RECT_RE.search(s or "")
    return tuple(int(g) for g in m.groups()) if m else (0, 0, 0, 0)

import re

_ALIAS_RE = re.compile(rb"([A-Za-z0-9_\-]+)/([A-Za-z0-9_\-.]+)")

def _skel_alias_map(source_dir: Path):
    aliases = {}
    for sk in source_dir.rglob("*.skel"):
        try:
            b = sk.read_bytes()
        except Exception:
            continue
        for m in _ALIAS_RE.finditer(b):
            pre = m.group(1).decode("latin1")
            name = m.group(2).decode("latin1")
            if name.endswith((".png", ".jpg")):
                name = name.rsplit(".", 1)[0]
            aliases.setdefault(name, set()).add(pre)
    return aliases

def _region_name(key: str) -> str:
    return key.rsplit(".", 1)[0]


def plist_to_atlas(plist_path: Path, out_path: Path, texture_name: str = None, aliases: dict = None) -> int:
    d = plistlib.load(open(plist_path, "rb"))
    meta = d.get("metadata", {}) or {}
    frames = d.get("frames", {})
    if not frames:
        return 0
    tex = texture_name or meta.get("realTextureFileName") or meta.get("textureFileName") or (plist_path.stem + ".png")
    pw, ph = _size(meta.get("size"))
    if pw <= 0 or ph <= 0:
        pw = max((_rect(f.get("textureRect"))[0] + _rect(f.get("textureRect"))[2] for f in frames.values()), default=0)
        ph = max((_rect(f.get("textureRect"))[1] + _rect(f.get("textureRect"))[3] for f in frames.values()), default=0)
    lines = ["", tex, f"size: {pw}, {ph}", "format: RGBA8888", "filter: Linear, Linear", "repeat: none"]
    for key in sorted(frames):
        f = frames[key]
        rect_s = f.get("textureRect") or f.get("frame") or ""
        x, y, w, h = _rect(rect_s)
        rotated = bool(f.get("textureRotated", f.get("rotated", False)))
        ow, oh = _size(f.get("spriteSourceSize") or f.get("sourceSize") or "") or _size(f.get("spriteSize")) or (w, h)
        dx, dy = _size(f.get("spriteOffset") or f.get("offset"))
        # 裁剪内容左上角相对原图(原点在左上、y 向下)
        ox = dx if not rotated else dy
        oy = dy if not rotated else dx
        off_x = ow / 2 - ox - w / 2
        off_y = oh / 2 - oy - h / 2
        off_x = int(round(off_x))
        off_y = int(round(off_y))
        base = _region_name(key)
        names = [base]
        for pre in sorted((aliases or {}).get(base, ())):
            names.append(f"{pre}/{base}")
        for nm in names:
            lines.append(nm)
            lines.append(f"  rotate: {'true' if rotated else 'false'}")
            lines.append(f"  xy: {x}, {y}")
            lines.append(f"  size: {w}, {h}")
            lines.append(f"  orig: {ow}, {oh}")
            lines.append(f"  offset: {off_x}, {off_y}")
            lines.append("  index: -1")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(frames)


def solve(source_dir: Path, output_dir: Path = None, only_with_skel: bool = False, delete_source: bool = False):
    aliases = _skel_alias_map(source_dir) if source_dir.exists() else {}
    if output_dir is None:
        output_dir = source_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for pl in source_dir.rglob("*.plist"):
        if only_with_skel and not (pl.parent / (pl.stem + ".skel")).exists():
            continue
        if output_dir is None:
            out = pl.with_suffix(".atlas")
        else:
            out = output_dir / pl.relative_to(source_dir).with_suffix(".atlas")
            out.parent.mkdir(parents=True, exist_ok=True)
        try:
            cnt = plist_to_atlas(pl, out, aliases=aliases)
        except Exception as e:
            print(f"[FAIL] {pl}: {e}")
            continue
        if cnt:
            if delete_source:
                pl.unlink()
                # print(f"[DEL] {pl}")
            n += 1
    print(f"done: {n}")


if __name__ == "__main__":
    SOURCE_DIR = Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\illusionConnectRe\output\asset")
    OUTPUT_DIR = None
    ONLY_WITH_SKEL = False
    DELETE_SOURCE = False
    solve(SOURCE_DIR, OUTPUT_DIR, ONLY_WITH_SKEL, DELETE_SOURCE)
