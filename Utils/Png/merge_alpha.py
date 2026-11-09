import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

WORKERS = min(32, os.cpu_count() or 8)
PNG_COMPRESS_LEVEL = 1


def _valid_image(path: Path) -> bool:
    try:
        with Image.open(path) as im:
            im.verify()
        return True
    except Exception:
        return False


def _merge(base: Path, alpha: Path, target: Path, compress_level: int, delete_source: bool):
    try:
        with Image.open(base) as b, Image.open(alpha) as a:
            rgb = b.convert("RGB")
            al = a.convert("L")
            if al.size != rgb.size:
                al = al.resize(rgb.size)
            Image.merge("RGBA", (*rgb.split(), al)).save(
                target, format="PNG", compress_level=compress_level
            )
        if delete_source:
            if base.resolve() != target.resolve():
                base.unlink()
            alpha.unlink()
        return "ok", target
    except Exception as e:
        return "fail", f"{alpha}: {e}"


def merge_alpha_images(root: Path,
                       base_exts=(".png", ".jpg", ".jpeg", ".webp"),
                       alpha_suffixes=("_alpha.png", "_a.png", ".png@alpha"),
                       delete_source=False,
                       workers=WORKERS,
                       compress_level=PNG_COMPRESS_LEVEL):
    tasks = []
    missing = bad = 0
    for alpha in root.rglob("*"):
        suffix = next((s for s in alpha_suffixes if alpha.name.endswith(s)), None)
        if not suffix:
            continue
        name = alpha.name[:-len(suffix)]
        base = next((alpha.parent / (name + ext) for ext in base_exts
                     if (alpha.parent / (name + ext)).exists()), None)
        if base is None:
            missing += 1
            continue
        if not _valid_image(alpha) or not _valid_image(base):
            print(f"[SKIP] 非图片残留: {alpha.name}（建议删除后重跑解密/合并）")
            bad += 1
            continue
        target = alpha.parent / (name + ".png")
        if target.exists() and target != base:
            continue
        tasks.append((base, alpha, target))

    ok = fail = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for status, info in pool.map(
            lambda t: _merge(t[0], t[1], t[2], compress_level, delete_source), tasks
        ):
            if status == "ok":
                ok += 1
            else:
                print(f"[FAIL] {info}")
                fail += 1
    print(f"done: ok={ok} fail={fail} 跳过非图片={bad} 缺主图={missing}")


if "__main__" == __name__:
    TARGET_DIR = Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\illusionConnectRe\output")

    BASE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".webp"]
    ALPHA_SUFFIXES = [
        "_alpha.png",
        "_a.png",
        ".png@alpha"
    ]

    merge_alpha_images(
        root=TARGET_DIR,
        base_exts=BASE_EXTENSIONS,
        alpha_suffixes=ALPHA_SUFFIXES,
        delete_source=True
    )
