#!/usr/bin/env python3

import os
from pathlib import Path

def main():
    current_dir = Path(".").resolve()
    print(f"扫描空目录: {current_dir}")
    
    empty_dirs = []
    
    # 从最深层的目录开始扫描
    for root, dirs, files in os.walk(current_dir, topdown=False):
        current_path = Path(root)
        
        # 跳过当前目录本身
        if current_path == current_dir:
            continue
            
        # 检查目录是否为空
        if not any(current_path.iterdir()):
            empty_dirs.append(current_path)
    
    if not empty_dirs:
        print("没有发现空目录。")
        return
    
    print(f"\n发现 {len(empty_dirs)} 个空目录:")
    for dir_path in empty_dirs:
        print(f"  - {dir_path.relative_to(current_dir)}")
    
    confirm = input("\n确认删除这些空目录？(y/N): ").strip().lower()
    if confirm in ['y', 'yes']:
        deleted_count = 0
        for dir_path in empty_dirs:
            try:
                dir_path.rmdir()
                print(f"✓ 删除: {dir_path.relative_to(current_dir)}")
                deleted_count += 1
            except OSError as e:
                print(f"✗ 删除失败: {dir_path.relative_to(current_dir)} - {e}")
        print(f"\n删除完成。共删除 {deleted_count} 个空目录。")
    else:
        print("操作已取消。")

if __name__ == "__main__":
    main()