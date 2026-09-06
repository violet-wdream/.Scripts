#!/usr/bin/env python3
import os

# ====== 配置区 ======
INPUT_PATH = r"D:\Tools\UsefulTools\MuMu\Shared\Download\resources\output"
SrcEXT = ".bin"      # 源扩展名（可包含多个点）
DstEXT = ".skel"                # 目标扩展名
DRY_RUN = False
# ====================

# 确保扩展名以点开头（但保留多段）
if not SrcEXT.startswith('.'):
    SrcEXT = '.' + SrcEXT
if not DstEXT.startswith('.'):
    DstEXT = '.' + DstEXT

count = 0

for root, _, files in os.walk(INPUT_PATH):
    for file in files:
        filepath = os.path.join(root, file)

        if os.path.islink(filepath):
            continue

        # 检查文件名是否以 SrcEXT 结尾（忽略大小写）
        if file.lower().endswith(SrcEXT.lower()):
            # 去掉源扩展名，得到基础名
            base = file[:-len(SrcEXT)]
            new_filename = base + DstEXT
            new_path = os.path.join(root, new_filename)

            # 处理目标文件已存在的情况
            if os.path.exists(new_path):
                src_size = os.path.getsize(filepath)
                dst_size = os.path.getsize(new_path)

                if src_size > dst_size:
                    action = f"[覆盖] 保留源文件 {filepath}"
                    if not DRY_RUN:
                        os.remove(new_path)
                        os.rename(filepath, new_path)
                else:
                    action = f"[跳过] 目标文件更大 {new_path}"
                    if not DRY_RUN:
                        os.remove(filepath)

                print(action)

            else:
                if DRY_RUN:
                    print(f"[模拟] {filepath} -> {new_path}")
                else:
                    try:
                        os.rename(filepath, new_path)
                        print(f"{filepath} -> {new_path}")
                    except OSError as e:
                        print(f"错误: {filepath} - {e}")
                        continue

            count += 1

print(f"\n完成，共处理 {count} 个文件。")