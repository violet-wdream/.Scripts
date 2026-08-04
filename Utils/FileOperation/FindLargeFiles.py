#!/usr/bin/env python3
import os
from pathlib import Path

# ===== 配置 =====
ROOT_DIR = r"D:\Tools\UsefulTools\MuMu\Shared\Download\illusionConnectRe"   # 指定搜索目录
TOP_N = 10               # 取前 N 个最大文件
EXCLUDE_EXTENSIONS = ['.png', '.jpg', '.webp', '.astc', '.mp3', '.mp4', '.ttf', '.binary']  # 要排除的文件后缀
INCLUDE_EXTENSIONS = ['.zip']

def top_n_files_by_size(root, n):

    files = []

    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            path = Path(dirpath) / name
            
            if EXCLUDE_EXTENSIONS:
                ext = path.suffix.lower()
                if ext in EXCLUDE_EXTENSIONS:
                    continue
            if INCLUDE_EXTENSIONS:
                ext = path.suffix.lower()
                if ext not in INCLUDE_EXTENSIONS:
                    continue
            
            try:
                size = path.stat().st_size
                files.append((path, size))
            except (PermissionError, FileNotFoundError):
                continue

    files.sort(key=lambda x: x[1], reverse=True)
    return files[:n]

if __name__ == "__main__":
    print(f"搜索目录: {ROOT_DIR}")
    print(f"最大文件数: {TOP_N}")
    if EXCLUDE_EXTENSIONS:
        print(f"排除的后缀: {', '.join(EXCLUDE_EXTENSIONS)}")
    if INCLUDE_EXTENSIONS:
        print(f"包含的后缀: {', '.join(INCLUDE_EXTENSIONS)}")
    print("-" * 80)
    
    results = top_n_files_by_size(ROOT_DIR, TOP_N)
    
    if results:
        for i, (path, size) in enumerate(results, 1):
            print(f"{i:2d}. {path} | {path.name} | {round(size / (1024 * 1024), 1)} MB")
    else:
        print("未找到符合条件的文件")