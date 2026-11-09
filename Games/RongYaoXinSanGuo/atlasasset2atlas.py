from __future__ import annotations

import re
import struct
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


# ---------------------------------------------------------------------------
# Binary format
# ---------------------------------------------------------------------------

@dataclass
class Region:
    name: str
    x: int
    y: int
    w: int
    h: int
    u: float
    v: float
    u2: float
    v2: float
    off_x: int
    off_y: int
    orig_w: int
    orig_h: int
    index: int
    rotated: bool
    flags: int


@dataclass
class AtlasAsset:
    asset_name: str
    image: str
    version: int
    meta: list[int]
    page_w: int
    page_h: int
    regions: list[Region] = field(default_factory=list)


def _read_string(buf: bytes, offset: int) -> tuple[str, int]:
    if offset + 4 > len(buf):
        raise ValueError("truncated string length")

    length = struct.unpack_from("<i", buf, offset)[0]
    if not 0 <= length <= 4096:
        raise ValueError(f"invalid string length: {length}")

    end = offset + 4 + length
    if end > len(buf):
        raise ValueError("truncated string data")

    value = buf[offset + 4:end].decode("utf-8")
    return value, offset + ((4 + length + 3) // 4) * 4


def parse_atlas_asset(buf: bytes) -> AtlasAsset:
    """Parse the raw bytes of a SkeletonAtlasFileAsset MonoBehaviour."""
    if len(buf) < 116:
        raise ValueError("file too small")

    offset = 28
    asset_name, offset = _read_string(buf, offset)
    offset += 4
    image_name, offset = _read_string(buf, offset)

    if offset + 32 > len(buf):
        raise ValueError("truncated page header")

    version, m1, m2, m3, m4, page_w, page_h, count = struct.unpack_from("<8i", buf, offset)
    offset += 32

    if not 0 < count <= 100000:
        raise ValueError(f"invalid region count: {count}")
    if page_w <= 0 or page_h <= 0:
        raise ValueError(f"invalid page size: {page_w}x{page_h}")

    regions: list[Region] = []
    for _ in range(count):
        name, offset = _read_string(buf, offset)
        if offset + 64 > len(buf):
            raise ValueError("truncated region record")

        x, y, w, h = struct.unpack_from("<4i", buf, offset)
        u, v, u2, v2 = struct.unpack_from("<4f", buf, offset + 16)
        off_x, off_y, orig_w, orig_h = struct.unpack_from("<4i", buf, offset + 32)
        index, rotated, flags = struct.unpack_from("<3i", buf, offset + 48)

        if w < 0 or h < 0:
            raise ValueError(f"invalid region size for {name}: {w}x{h}")

        pw, ph = (h, w) if rotated else (w, h)
        if x < 0 or y < 0 or x + pw > page_w or y + ph > page_h:
            raise ValueError(f"region out of page: {name}")

        regions.append(Region(
            name, x, y, w, h, u, v, u2, v2,
            off_x, off_y, orig_w, orig_h,
            index, bool(rotated), flags,
        ))
        offset += 64

    if offset != len(buf):
        raise ValueError(f"{len(buf) - offset} trailing bytes")

    return AtlasAsset(
        asset_name, image_name, version, [m1, m2, m3, m4],
        page_w, page_h, regions,
    )


# ---------------------------------------------------------------------------
# Bundle input
# ---------------------------------------------------------------------------

def _patch_unitypy_version_parser() -> None:
    """Fix Unity version strings containing newlines."""
    try:
        from UnityPy.helpers import UnityVersion as UV
    except Exception:
        return

    original = getattr(UV.UnityVersion.from_str, "__func__", UV.UnityVersion.from_str)

    def from_str(cls, version):
        return original(cls, str(version).strip().split("\n")[0].strip())

    UV.UnityVersion.from_str = classmethod(from_str)


def read_bundle(path: Path) -> list[AtlasAsset]:
    try:
        import UnityPy
    except ImportError as exc:
        raise RuntimeError("读取 .bundle 需要 UnityPy，请先安装：pip install UnityPy") from exc

    _patch_unitypy_version_parser()

    assets: list[AtlasAsset] = []
    for obj in UnityPy.load(str(path)).objects:
        if obj.type.name != "MonoBehaviour":
            continue
        try:
            assets.append(parse_atlas_asset(obj.get_raw_data()))
        except Exception:
            continue
    return assets


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def build_atlas_text(data: AtlasAsset) -> str:
    image = data.image.replace("\ufeff", "").strip()

    lines = [
        image,
        f"size: {data.page_w},{data.page_h}",
        "format: RGBA8888",
        "filter: Linear,Linear",
        "repeat: none",
    ]

    for r in data.regions:
        lines += [
            r.name,
            f"  rotate: {'true' if r.rotated else 'false'}",
            f"  xy: {r.x}, {r.y}",
            f"  size: {r.w}, {r.h}",
            f"  orig: {r.orig_w}, {r.orig_h}",
            f"  offset: {r.off_x}, {r.off_y}",
            f"  index: {r.index}",
        ]

    return "\n" + "\n".join(lines) + "\n"


def safe_stem(name: str) -> str:
    stem = re.sub(r"AtlasAsset$", "", name, flags=re.IGNORECASE)
    stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", stem).strip(" .")
    return stem or "atlas"


def write_outputs(data: AtlasAsset, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    atlas_path = out_dir / f"{safe_stem(data.asset_name)}.atlas"
    atlas_path.write_text(build_atlas_text(data), encoding="utf-8", newline="\n")
    return atlas_path


# ---------------------------------------------------------------------------
# Process
# ---------------------------------------------------------------------------

def solve(source: Path, output_dir: Path) -> None:
    suffix = source.suffix.lower()

    if suffix == ".dat":
        assets = [parse_atlas_asset(source.read_bytes())]
    elif suffix in (".bundle", ".ab") and "atlasasset" in source.name.lower():
        assets = read_bundle(source)
    else:
        return

    for data in assets:
        write_outputs(data, output_dir)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    SOURCE_DIR = Path(r"C:\Users\86182\Downloads\TEMP\test\atlasAsset")
    OUTPUT_DIR = Path(r"C:\Users\86182\Downloads\TEMP\test\atlas")

    for p in SOURCE_DIR.rglob("*"):
        if not p.is_file():
            continue
        try:
            solve(p, OUTPUT_DIR)
            print(f"[OK] {p}")
        except Exception as e:
            print(f"[FAIL] {p}: {e}")