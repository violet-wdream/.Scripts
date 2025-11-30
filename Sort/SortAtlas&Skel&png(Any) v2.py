#!/usr/bin/env python3

import os
import shutil
from pathlib import Path

# === 配置 ===
DRYRUN = False  # True = 仅显示，不移动；False = 执行移动

def main():
    src_dir = Path(".").resolve()
    print(f"[INFO] 工作目录: {src_dir}")
    
    # 优化 1: 一次性扫描所有文件和 atlas 文件
    print("[INFO] 正在扫描所有文件和 atlas 文件...")
    
    # 收集所有文件 (用于匹配)
    all_files_map = {}
    
    # 收集所有 atlas 文件及其路径信息
    atlas_info = []
    
    for item in src_dir.rglob("*"):
        if item.is_file():
            # 存储文件的 stem (用于匹配) 到文件的 Path 对象
            # 键格式: (parent_path, stem)
            all_files_map[(item.parent, item.stem)] = item
            
            if item.suffix == '.atlas':
                # 存储 atlas 信息
                atlas_info.append({
                    'name': item.stem,
                    'parent': item.parent,
                    'path': item
                })
        
    print(f"[INFO] 找到 {len(atlas_info)} 个 atlas 文件，共 {len(all_files_map)} 个文件。")
    
    if not atlas_info:
        print("[INFO] 未找到 atlas 文件。")
        return

    files_to_move = []
    target_dirs_to_create = set() # 存储需要创建的目录路径，防止重复 I/O

    # 2. 基于 atlas 信息进行匹配和收集移动操作
    for info in atlas_info:
        name = info['name']
        parent_dir = info['parent']
        
        target_dir = parent_dir / name
        target_dirs_to_create.add(target_dir) # 收集待创建的目录
        
        # 遍历 atlas 文件所在目录的所有文件进行匹配
        for key, file_path in all_files_map.items():
            
            # 确保文件在 atlas 所在的目录中 (key[0] 是 parent_path)
            if key[0] != parent_dir:
                continue

            # 匹配逻辑 (与您原脚本中的逻辑相同)
            is_match = False
            f_stem = file_path.stem 
            
            if f_stem == name:
                is_match = True
            elif f_stem.startswith(name) and len(f_stem) > len(name):
                next_char = f_stem[len(name)]
                if next_char in [' ', '#', '_', '-', '.']:
                    is_match = True
            
            if is_match:
                # 检查是否已经在目标目录中
                if file_path.parent != target_dir:
                    files_to_move.append((file_path, target_dir))

    # 3. 优化 2: 批量创建目录 (只执行一次检查和创建操作)
    print(f"\n[INFO] 正在批量创建 {len(target_dirs_to_create)} 个目标目录...")
    if not DRYRUN:
        for t_dir in target_dirs_to_create:
            if not t_dir.exists():
                t_dir.mkdir(parents=True, exist_ok=True)
    
    # === 执行部分 ===
    if not files_to_move:
        print("没有找到需要移动的文件。")
        return
    
    # ... (移动文件的逻辑保持不变，确保确认步骤在创建目录之后) ...

    print(f"\n找到 {len(files_to_move)} 个待移动文件：")
    
    # 排序并打印
    files_to_move.sort(key=lambda x: x[0].name)
    
    for i, (src, dst) in enumerate(files_to_move):
        if i < 10: 
            try:
                print(f"  {src.relative_to(src_dir)} -> {dst.relative_to(src_dir)}/")
            except ValueError:
                 print(f"  {src.name} -> {dst.name}/")
                 
    if len(files_to_move) > 10: print(f"  ... (共 {len(files_to_move)} 个)")
    
    confirm = input("\n确认执行移动操作？(y/N) ").strip().lower()
    if confirm in ['y', 'yes']:
        count = 0
        for src, dst in files_to_move:
            try:
                dst_file = dst / src.name
                if dst_file.exists():
                    print(f"[跳过] 目标存在: {src.name}")
                    continue
                
                print(f"移动: {src.name} -> {dst.name}/")
                if not DRYRUN:
                    shutil.move(str(src), str(dst))
                count += 1
            except Exception as e:
                print(f"[错误] 移动 {src.name} 失败: {e}")
        print(f"完成，已移动 {count} 个文件。")
    else:
        print("操作已取消。")

if __name__ == "__main__":
    main()