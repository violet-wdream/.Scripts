#!/usr/bin/env python3

import os
import shutil
from pathlib import Path

# === 配置 ===
DRYRUN = False  # True = 仅显示，不移动；False = 执行移动

def main():
    src_dir = Path(".").resolve()
    print(f"[INFO] 工作目录: {src_dir}")
    
    files_to_move = []
    
    # 扫描所有 atlas 文件（包括子目录）
    atlas_files = list(src_dir.rglob("*.atlas"))
    
    if atlas_files:
        print(f"[INFO] 找到 {len(atlas_files)} 个 atlas 文件")
        
        # 基于 atlas 文件进行归类
        for atlas_path in atlas_files:
            name = atlas_path.stem
            parent_dir = atlas_path.parent
            
            print(f"[DEBUG] 处理 atlas: {atlas_path.relative_to(src_dir)}")
            
            # 创建目标目录
            target_dir = parent_dir / name
            if not target_dir.exists() and not DRYRUN:
                target_dir.mkdir(parents=True, exist_ok=True)
                print(f"[DEBUG] 创建目录: {target_dir.relative_to(src_dir)}")
            
            # 查找同目录下与 atlas 同名的所有文件（包括 atlas 文件本身）
            for file_path in parent_dir.iterdir():
                if file_path.is_file() and name in file_path.stem:
                    # 检查是否已经在目标目录中，避免重复移动
                    if file_path.parent != target_dir:
                        files_to_move.append((file_path, target_dir))
                        print(f"[DEBUG] 找到匹配文件: {file_path.name}")
    
    else:
        # 没有 atlas 文件，按目录名归类
        print("[INFO] 未找到 atlas 文件，使用目录名匹配模式")
        existing_dirs = [d for d in src_dir.rglob("*") if d.is_dir()]
        
        for file_path in src_dir.rglob("*"):
            if file_path.is_file():
                file_stem = file_path.stem.split('#')[0]
                
                # 查找匹配的目录
                for existing_dir in existing_dirs:
                    if file_stem.startswith(existing_dir.name):
                        # 确保文件不在目标目录中
                        if file_path.parent != existing_dir:
                            files_to_move.append((file_path, existing_dir))
                        break
    
    # 显示并执行移动
    if not files_to_move:
        print("没有找到需要移动的文件。")
        return
    
    print(f"\n找到 {len(files_to_move)} 个待移动文件：")
    for src, dst in files_to_move:
        print(f"  {src.relative_to(src_dir)} -> {dst.relative_to(src_dir)}/")
    
    confirm = input("\n确认执行移动操作？(y/N) ").strip().lower()
    if confirm in ['y', 'yes']:
        moved_count = 0
        for src_path, dst_dir in files_to_move:
            try:
                print(f"移动: {src_path.name} -> {dst_dir.name}/")
                if not DRYRUN:
                    shutil.move(str(src_path), str(dst_dir))
                moved_count += 1
            except Exception as e:
                print(f"错误: 移动 {src_path.name} 失败: {e}")
        print(f"移动完成。共移动 {moved_count} 个文件。")
    else:
        print("操作已取消。")

if __name__ == "__main__":
    main()