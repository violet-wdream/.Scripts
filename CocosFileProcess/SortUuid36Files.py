import os
import shutil
import json
from pathlib import Path
from collections import defaultdict

# ---------- Config ----------
CONFIG_PATH = Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\resources\config.json")
INPUT_DIR = Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\resources\native")
OUTPUT_DIR = Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\resources\output")
# --------------------------




BASE64_KEYS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
HEX_CHARS = "0123456789abcdef"


def compress_uuid(full_uuid: str) -> str:
    parts = full_uuid.split('@')
    uuid_part = parts[0]
    suffix_part = '@' + parts[1] if len(parts) > 1 else ''

    if len(uuid_part) != 36:
        return full_uuid

    clean_uuid = uuid_part.replace("-", "")
    hex_map = {c: i for i, c in enumerate(HEX_CHARS)}
    zip_uuid = [uuid_part[0], uuid_part[1]]

    for i in range(2, 32, 3):
        left = hex_map[clean_uuid[i]]
        mid = hex_map[clean_uuid[i + 1]]
        right = hex_map[clean_uuid[i + 2]]

        zip_uuid.append(BASE64_KEYS[(left << 2) + (mid >> 2)])
        zip_uuid.append(BASE64_KEYS[((mid & 3) << 4) + right])

    return ''.join(zip_uuid) + suffix_part


def main():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)

    uuid22_to_path = {}
    uuids = config.get("uuids", [])
    paths_dict = config.get("paths", {})

    for uuidIndex, path in paths_dict.items():
        idx = int(uuidIndex)
        if idx < len(uuids):
            uuid22 = uuids[idx]
            path_str = path[0]
            uuid22_to_path[uuid22] = path_str

    print(f"[INFO] 映射表生成完成，共 {len(uuid22_to_path)} 条")

    groups = defaultdict(list)  # dst_path -> [(src_path, size)]
    not_found_files = []

    for root, _, files in os.walk(INPUT_DIR):
        for file in files:
            name, ext = os.path.splitext(file)
            ext = ext.lower()

            if len(name) >= 36:
                uuid22 = compress_uuid(name)
            else:
                uuid22 = name

            if uuid22 not in uuid22_to_path:
                not_found_files.append(file)
                continue

            orig_path = uuid22_to_path[uuid22]
            dir_path, logical_name = os.path.split(orig_path)

            target_dir = OUTPUT_DIR / dir_path
            dst_file = target_dir / f"{logical_name}{ext}"

            src_file = Path(root) / file
            size = src_file.stat().st_size

            groups[dst_file].append((src_file, size))

    print(f"[INFO] 收集完成，共 {len(groups)} 个目标路径")

    for dst_file, items in groups.items():
        # 按 size 降序
        items.sort(key=lambda x: x[1], reverse=True)

        best_src, best_size = items[0]

        if len(items) > 1:
            print(f"[CONFLICT] {dst_file} ← {len(items)} 个文件，仅保留最大(size={best_size})")

        dst_file.parent.mkdir(parents=True, exist_ok=True)

        # 移动最大文件
        # print(f"[MOVE] {best_src} -> {dst_file}")
        shutil.move(best_src, dst_file)

        # 删除其余文件
        for src_file, size in items[1:]:
            print(f"[DROP] {src_file} (size={size})")
            # try:
            #     os.remove(src_file)
            # except Exception as e:
            #     print(f"[ERROR] 删除失败: {src_file} | {e}")

    print(f"[INFO] 完成，{len(not_found_files)} 个文件未找到映射")
    if not_found_files:
        print("[WARN] 未匹配文件：")
        for f in not_found_files:
            print(" ", f)


if __name__ == "__main__":
    main()