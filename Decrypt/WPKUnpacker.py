#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 6.29版本bandizip命令行工具 bc.exe 解压 .wpk 文件
import os
from pathlib import Path
import subprocess
import argparse

# 直接用 "bc"，系统会自动在 PATH 中查找
CMD = "bc"         

def unpack(wpk_path: Path, delete_source: bool):
    # 移除手动创建的空目录，让 bc.exe 使用其默认行为
    # out_dir = wpk_path.parent / wpk_path.stem 
    # out_dir.mkdir(exist_ok=True) 

    # 构造命令：只包含指令、归档路径和覆盖开关
    cmd = [
        CMD,
        "x",             # 全路径解压
        str(wpk_path),        # 归档文件路径
        "-y"             # 覆盖不询问
    ]

    print(f"解压 → {wpk_path.name} (到 bc.exe 的默认路径)")

    try:
        # 添加 creationflags=subprocess.CREATE_NO_WINDOW 以隐藏命令行窗口（原代码已有）
        result = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode == 0:
            print(f"成功 → {wpk_path.name}")
            if delete_source:
                # 注意：如果文件解压到当前目录，您创建的同名空目录（如果没删除）依然会在
                wpk_path.unlink()
                print(f"已删除源文件 → {wpk_path.name}")
            return True
        else:
            print(f"失败（错误码 {result.returncode}）: {wpk_path.name}")
            if result.stdout:
                 print("--- bc.exe STDOUT ---")
                 print(result.stdout.strip())
            if result.stderr:
                print(result.stderr.strip())
            return False
    except Exception as e:
        print(f"异常: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="使用系统 bc.exe 批量解压所有 .wpk")
    parser.add_argument("-d", "--delete", action="store_true", help="解压后删除源文件")
    args = parser.parse_args()

    files = list(Path(".").rglob("*.wpk"))
    if not files:
        print("没找到 .wpk 文件")
        input("按回车退出...")
        return

    print(f"发现 {len(files)} 个 .wpk 文件，开始解压...\n")
    success = 0
    for f in files:
        if unpack(f, args.delete):
            success += 1

    print(f"\n全部完成！成功 {success}/{len(files)} 个")
    input("按回车任意键退出...")

if __name__ == "__main__":
    main()