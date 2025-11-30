#!/usr/bin/env python3

import os
import shutil
from pathlib import Path

# === 配置项 ===
# True = 仅显示操作，不执行任何移动操作 (建议先使用 DRYRUN 模式！)
# False = 实际执行文件移动
DRYRUN = False 

# 提取文件存放的目标目录名称 
# 所有找到的文件都将被移动到此目录中
TARGET_DIR_NAME = "_extracted_files"

def main():
    # 获取当前工作目录
    src_dir = Path(".").resolve()
    target_dir = src_dir / TARGET_DIR_NAME
    
    print(f"==================================================")
    print(f"工作目录: {src_dir}")
    print(f"目标提取目录: {target_dir}")
    print(f"DRY RUN (模拟模式): {DRYRUN}")
    print(f"==================================================")
    
    files_to_move = []
    
    # 1. 扫描并收集所有需要移动的文件
    # 使用 rglob("*") 递归查找所有文件和目录
    for item in src_dir.rglob("*"):
        
        # 跳过目标目录（如果已经存在）
        if item.is_relative_to(target_dir):
            continue
            
        if item.is_file():
            # 目标文件路径。注意：使用 item.name 来避免路径冲突
            dst_path = target_dir / item.name
            files_to_move.append((item, dst_path))
    
    if not files_to_move:
        print("[INFO] 当前目录下没有找到需要提取的文件。")
        return
    
    # --- 移动文件步骤 ---
    print(f"\n--- 步骤: 移动文件 (共 {len(files_to_move)} 个文件) ---")

    if not DRYRUN:
        # 确保目标目录存在
        target_dir.mkdir(exist_ok=True)
    
    moved_count = 0
    # 由于文件名可能冲突，我们使用一个集合来跟踪目标目录中已经处理过的文件名
    # 确保不会覆盖已有文件
    existing_target_files = set(p.name for p in target_dir.iterdir()) if target_dir.exists() else set()
    
    for src_path, dst_path in files_to_move:
        # 检查文件名是否已在目标目录中存在
        if dst_path.name in existing_target_files:
            print(f"[跳过] 目标已存在且文件名冲突: {src_path.name}")
            continue
            
        print(f"[移动] {src_path.relative_to(src_dir)} -> {target_dir.name}/{dst_path.name}")
        
        if not DRYRUN:
            try:
                # 使用 rename 来移动文件
                src_path.rename(dst_path) 
                # 移动成功后，更新集合以防止后续冲突
                existing_target_files.add(dst_path.name)
                moved_count += 1
            except Exception as e:
                print(f"[错误] 移动 {src_path.name} 失败: {e}")    
    if DRYRUN:
        print("\n*** 当前处于模拟模式 (DRYRUN=True)，未执行任何实际操作。***")
        print("*** 确认无误后，请将脚本中的 DRYRUN 设置为 False 再运行。***")

if __name__ == "__main__":
    main()