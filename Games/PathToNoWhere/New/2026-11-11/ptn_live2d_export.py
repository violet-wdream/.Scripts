# 2026-11-11
#!/usr/bin/env python3
"""PTN Live2D batch exporter.

Edit INPUT_PATH / OUTPUT_PATH at the bottom and run:
    python ptn_live2d_export.py

Output:
    <output>/<ModelName>/<ModelName>.moc3
    <output>/<ModelName>/<ModelName>.model3.json
    <output>/<ModelName>/textures/*.png
    <output>/<ModelName>/motions/*.motion3.json
"""
from __future__ import annotations

import json
import math
import re
import time
from pathlib import Path

from Live2DFileConvert.motion3.Anim2motion3 import build_moc3_maps, animation_clip_to_motion
from Utils.Png.Texture2Png import decode_astc



def parse_3com(data: bytes) -> tuple[int, int]:
    """Return (moc3_offset, inner_unityfs_offset) from a 3COM wrapper."""
    magic = data.find(b"3COM", 0, 0x100)
    if magic < 0:
        raise ValueError("3COM header not found")
    moc = int.from_bytes(data[magic + 24:magic + 28], "little")
    inner = int.from_bytes(data[magic + 8:magic + 16], "little")
    if data[moc:moc + 4] != b"MOC3":
        raise ValueError("MOC3 magic not found")
    if data[inner:inner + 8] != b"UnityFS\0":
        raise ValueError("inner UnityFS not found")
    return moc, inner


def extract_moc3(data: bytes) -> bytes:
    """Extract the MOC3 block, including its 64-byte alignment padding."""
    moc, inner = parse_3com(data)
    return data[moc:inner]


def _patch_unitypy() -> None:
    try:
        from UnityPy.helpers import UnityVersion as UV
    except Exception:
        return
    if getattr(UV.UnityVersion, "_ptn_patched", False):
        return
    original = getattr(UV.UnityVersion.from_str, "__func__", UV.UnityVersion.from_str)

    def from_str(cls, version):
        return original(cls, str(version).strip().split("\n")[0].strip())

    UV.UnityVersion.from_str = classmethod(from_str)
    UV.UnityVersion._ptn_patched = True


def load_env(data: bytes):
    import UnityPy
    _patch_unitypy()
    return UnityPy.load(data)

ASTC_MAGIC = b"\x13\xAB\xA1\x5C"
ASTC_BLOCKS = {
    48: (4, 4), 49: (5, 5), 50: (6, 6), 51: (8, 8), 52: (10, 10), 53: (12, 12),
    54: (4, 4), 55: (5, 5), 56: (6, 6), 57: (8, 8), 58: (10, 10), 59: (12, 12),
}
def decode_texture(obj):
    from PIL import Image
    
    data = obj.read()
    width, height = int(data.m_Width), int(data.m_Height)
    fmt = int(data.m_TextureFormat)
    if fmt not in ASTC_BLOCKS:
        raise ValueError("expected ASTC texture, got format %d" % fmt)

    bw, bh = ASTC_BLOCKS[fmt]
    raw = bytes(data.get_image_data())
    size = math.ceil(width / bw) * math.ceil(height / bh) * 16

    # decode_astc expects a 16-byte .astc header before the raw blocks.
    header = (ASTC_MAGIC + bytes([bw, bh, 1])
              + width.to_bytes(3, "little")
              + height.to_bytes(3, "little")
              + b"\x01\x00\x00")
    image = decode_astc(header + raw[:size])

    # Unity texture data is bottom-up; Cubism pages are top-down.
    return image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)


# ---------------------------------------------------------------------------
# Index / matching
# ---------------------------------------------------------------------------

def build_index(ptn_dir: Path) -> dict:
    models, textures, animations = {}, [], []
    files = sorted(ptn_dir.glob("*.bundle"))
    started = time.time()

    for index, path in enumerate(files):
        try:
            buf = path.read_bytes()
            if len(buf) < 16 or not buf.startswith(b"UnityFS\0"):
                continue
            magic = buf.find(b"3COM", 0, 0x100)
            if magic >= 0:
                moc, inner = parse_3com(buf)
                env = load_env(buf[inner:])
                mono = next((o.read() for o in env.objects if o.type.name == "MonoBehaviour"), None)
                name = getattr(mono, "m_Name", None) if mono else None
                if name:
                    models[name] = {"file": path.name, "moc_offset": moc, "inner_offset": inner}
            else:
                inner = buf.find(b"UnityFS\0", 8)
                if inner < 0:
                    continue
                env = load_env(buf[inner:])
                ab, texs, clips = None, [], []
                for obj in env.objects:
                    if obj.type.name == "AssetBundle":
                        try:
                            ab = obj.read().m_Name
                        except Exception:
                            pass
                    elif obj.type.name == "Texture2D":
                        try:
                            d = obj.read()
                            texs.append({
                                "name": d.m_Name, "width": d.m_Width,
                                "height": d.m_Height, "format": d.m_TextureFormat,
                            })
                        except Exception:
                            pass
                    elif obj.type.name == "AnimationClip":
                        try:
                            clips.append({"name": obj.read().m_Name})
                        except Exception:
                            pass
                if texs:
                    textures.append({"file": path.name, "inner": inner, "ab": ab, "textures": texs})
                elif clips:
                    animations.append({"file": path.name, "inner": inner, "ab": ab, "clips": clips})
        except Exception:
            pass

        if (index + 1) % 400 == 0:
            print("[INDEX] %d/%d models=%d tex=%d anim=%d %.1fs" % (
                index + 1, len(files), len(models), len(textures), len(animations),
                time.time() - started,
            ))

    print("[INDEX] %d models, %d texture bundles, %d animation bundles, %.1fs" % (
        len(models), len(textures), len(animations), time.time() - started,
    ))
    return {"models": models, "textures": textures, "animations": animations}


def key_match(text: str | None, key: str) -> bool:
    return bool(text) and re.search(
        r"(^|[^a-z0-9])" + re.escape(key.lower()) + r"([^a-z0-9]|$)", text.lower()
    ) is not None


def pick_texture(textures: list[dict], key: str):
    candidates = [entry for entry in textures if key_match(entry["ab"], key)]
    if not candidates:
        return None
    return max(candidates, key=lambda entry: sum(
        tex["width"] * tex["height"] for tex in entry["textures"]
    ))


def pick_anim(animations: list[dict], key: str):
    candidates = [
        entry for entry in animations
        if key_match(entry["ab"], key) and "effect" not in (entry["ab"] or "").lower()
    ]
    if not candidates:
        return None
    exact = "art_live2d_characters_" + key + "_animation.bundle"
    for entry in candidates:
        if (entry["ab"] or "").lower() == exact.lower():
            return entry
    for entry in candidates:
        if "_animation.bundle" in (entry["ab"] or "").lower():
            return entry
    return candidates[0]


def motion_name(clip_name: str, key: str) -> str:
    prefix = "clip_" + key.lower() + "_"
    if clip_name.lower().startswith(prefix):
        suffix = clip_name[len(prefix):]
    else:
        match = re.match(r"^clip_([^_]+)_(.+)$", clip_name, re.IGNORECASE)
        suffix = match.group(2) if match else (
            clip_name[5:] if clip_name.lower().startswith("clip_") else clip_name
        )
    replacements = {
        "handleft": "HandLeft",
        "handright": "HandRight",
        "interactivearea": "InteractiveArea",
    }
    return "_".join(
        replacements.get(word.lower(), word[:1].upper() + word[1:])
        for word in suffix.split("_") if word
    ) or "Motion"


def safe(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .") or "model"


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def export_model(name: str, model: dict, index: dict, ptn_dir: Path, out_root: Path) -> dict:
    out_dir = out_root / safe(name)
    out_dir.mkdir(parents=True, exist_ok=True)

    data = (ptn_dir / model["file"]).read_bytes()
    moc = extract_moc3(data)
    moc_path = out_dir / (safe(name) + ".moc3")
    moc_path.write_bytes(moc)

    texture_refs = []
    texture_bundle = pick_texture(index["textures"], name)
    if texture_bundle:
        env = load_env((ptn_dir / texture_bundle["file"]).read_bytes()[texture_bundle["inner"]:])
        for obj in sorted(
            (obj for obj in env.objects if obj.type.name == "Texture2D"),
            key=lambda obj: (getattr(obj.read(), "m_Name", "") or ""),
        ):
            try:
                tex = obj.read()
                image = decode_texture(obj)
                tex_dir = out_dir / "textures"
                tex_dir.mkdir(exist_ok=True)
                filename = "%s_%d.png" % (safe(tex.m_Name or "texture"), image.width)
                image.save(tex_dir / filename, compress_level=1)
                texture_refs.append("textures/" + filename)
            except Exception as exc:
                print("  [TEX-FAIL]", name, type(exc).__name__, exc)

    motions = {}
    animation_bundle = pick_anim(index["animations"], name)
    if animation_bundle:
        try:
            env = load_env((ptn_dir / animation_bundle["file"]).read_bytes()[animation_bundle["inner"]:])
            
            clips = [
                obj.read()
                for obj in env.objects
                if obj.type.name == "AnimationClip"
            ]
            targets = {
                binding.path
                for clip in clips
                for binding in clip.m_ClipBindingConstant.genericBindings
            }
            
            params, parts = build_moc3_maps(moc_path, targets)
            
            motion_dir = out_dir / "motions"
            motion_dir.mkdir(exist_ok=True)
            used = set()
            
            for obj in env.objects:
                if obj.type.name != "AnimationClip":
                    continue
                clip = obj.read()
                mname = motion_name(clip.m_Name, name)
                base, suffix = mname, 2
                while mname in used:
                    mname = "%s_%d" % (base, suffix)
                    suffix += 1
                used.add(mname)
                motion = animation_clip_to_motion(clip, params, parts)
                if not motion["Curves"]:
                    continue
                filename = mname + ".motion3.json"
                (motion_dir / filename).write_text(
                    json.dumps(motion, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                motions.setdefault(mname, []).append({"File": "motions/" + filename})
        except Exception as exc:
            print("  [MOT-FAIL]", name, type(exc).__name__, exc)

    model3 = {
        "Version": 3,
        "Name": name,
        "FileReferences": {
            "Moc": safe(name) + ".moc3",
            "Textures": texture_refs,
            "Physics": None,
            "Motions": motions,
        },
    }
    (out_dir / (safe(name) + ".model3.json")).write_text(
        json.dumps(model3, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return {"textures": len(texture_refs), "motions": len(motions), "moc3": len(moc)}


def main(input_path: Path, output_path: Path) -> int:
    if not input_path.is_dir():
        print("PTN directory not found:", input_path)
        return 1
    output_path.mkdir(parents=True, exist_ok=True)
    index = build_index(input_path)

    names = sorted(index["models"])
    print("[EXPORT] %d models -> %s" % (len(names), output_path))

    success = 0
    for number, name in enumerate(names, 1):
        try:
            info = export_model(name, index["models"][name], index, input_path, output_path)
            print("[OK] %d/%d %s moc=%d tex=%d motions=%d" % (
                number, len(names), name, info["moc3"], info["textures"], info["motions"],
            ))
            success += 1
        except Exception as exc:
            print("[FAIL]", name, type(exc).__name__, exc)
    print("[EXPORT] done: %d/%d" % (success, len(names)))
    return 0 if success else 1


if __name__ == "__main__":
    INPUT_PATH = Path(r"C:\Users\86182\Downloads\TEMP\PTN") # .bundles
    OUTPUT_PATH = Path(r"C:\Users\86182\Downloads\TEMP\output\PTN_Live2D")

    raise SystemExit(main(INPUT_PATH, OUTPUT_PATH))
