#!/usr/bin/env python3
# 作用： 根据 atlas 文件内容整理 spine 相关文件（atlas、skel/json、png）到同名目录
import shutil
from pathlib import Path
from typing import Set

# === 配置 ===
INPUT_PATH = r"D:\Tools\UsefulTools\MuMu\Shared\Download\HeiDong_crypto\out"

DRYRUN = False   # True = 仅显示,不移动;False = 执行移动
# ============

def parse_atlas_pngs(atlas_path: Path) -> Set[str]:
    pngs = set()
    with atlas_path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line.lower().endswith(".png") and ":" not in line:
                pngs.add(line)
    return pngs



def main():
    src_dir = Path(INPUT_PATH).resolve()
    print(f"[INFO] 工作目录: {src_dir}")

    atlas_files = list(src_dir.glob("*.atlas"))

    # ===== 有 atlas：构建 spine 结构 =====
    if atlas_files:
        print(f"[INFO] 找到 {len(atlas_files)} 个 atlas")

        for atlas in atlas_files:
            spine_dir = src_dir / atlas.stem

            # 准备目录
            if not DRYRUN:
                spine_dir.mkdir(exist_ok=True)

            # 确定 atlas 读取路径（DRYRUN 时仍用原路径避免 FileNotFound）
            new_atlas_path = spine_dir / atlas.name
            atlas_read_path = new_atlas_path if not DRYRUN else atlas

            # 移动 atlas（非 DRYRUN）
            if not DRYRUN:
                shutil.move(atlas, new_atlas_path)
            else:
                print(f"[DRYRUN] {atlas.name} -> {spine_dir.name}/")
            
            # 同名 skel / json
            for ext in (".skel", ".json"):
                f = src_dir / f"{atlas.stem}{ext}"
                if f.exists():
                    if not DRYRUN:
                        shutil.move(f, spine_dir / f.name)
                    else:
                        print(f"[DRYRUN] {f.name} -> {spine_dir.name}/")

            # atlas 引用的 png
            pngs = parse_atlas_pngs(atlas_read_path)
            for png_name in pngs:
                png_path = src_dir / png_name
                if png_path.exists():
                    if not DRYRUN:
                        shutil.move(png_path, spine_dir / png_name)
                    else:
                        print(f"[DRYRUN] {png_name} -> {spine_dir.name}/")
                else:
                    print(f"[WARN] atlas 引用的 png 缺失: {png_name}")

    else:
        print("[INFO] 根目录无 atlas，扫描子目录 atlas 进行归类")

        # 收集所有 atlas（含子目录）
        all_atlas = list(src_dir.rglob("*.atlas"))
        atlas_png_map = {}

        for atlas in all_atlas:
            try:
                atlas_png_map[atlas] = parse_atlas_pngs(atlas)
            except Exception as e:
                print(f"[WARN] 解析失败: {atlas} ({e})")

        # 根目录文件逐个处理
        for file in src_dir.iterdir():
            if not file.is_file():
                continue

            stem = file.stem
            suffix = file.suffix.lower()

            # ===== PNG：查 atlas =====
            if suffix == ".png":
                matched = []

                for atlas, pngs in atlas_png_map.items():
                    if file.name in pngs:
                        matched.append(atlas)

                if len(matched) == 1:
                    atlas = matched[0]
                    spine_dir = src_dir / atlas.stem
                    if not DRYRUN:
                        spine_dir.mkdir(exist_ok=True)
                        shutil.move(file, spine_dir / file.name)
                    print(f"[MOVE] {file.name} -> {spine_dir.name}/")

                elif len(matched) > 1:
                    print(f"[CONFLICT] {file.name} 被多个 atlas 引用:")
                    for a in matched:
                        print(f"  - {a}")

                else:
                    print(f"[UNUSED] {file.name} 未被任何 atlas 引用")

            # ===== skel / json：同名 =====
            elif suffix in (".skel", ".json"):
                target = src_dir / stem
                if target.is_dir():
                    if not DRYRUN:
                        shutil.move(file, target / file.name)
                    print(f"[MOVE] {file.name} -> {target.name}/")
                else:
                    print(f"[UNMATCHED] {file.name} 找不到对应 spine")

            # ===== 其他文件 =====
            else:
                print(f"[SKIP] {file.name}")                                    




if __name__ == "__main__":
    main()