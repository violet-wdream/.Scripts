#!/usr/bin/env python3
import os
import sys
import argparse

def add_extension_to_files(extension, dry_run=False):
    """
    给当前目录和子目录中没有后缀的文件添加指定后缀
    
    Args:
        extension (str): 要添加的后缀（如 ".txt"）
        dry_run (bool): 如果为True，只显示将要重命名的文件，不实际执行
    """
    if not extension.startswith('.'):
        extension = '.' + extension
    
    print(f"搜索目录: {os.getcwd()}")
    print(f"目标后缀: {extension}")
    print(f"模拟运行: {dry_run}")
    print("-" * 50)
    
    count = 0
    
    for root, dirs, files in os.walk('.'):
        for file in files:
            filepath = os.path.join(root, file)
            
            # 跳过符号链接
            if os.path.islink(filepath):
                continue
            
            # 检查文件是否有后缀
            name, ext = os.path.splitext(file)
            
            # 如果没有后缀或者只有点号
            if not ext or ext == '.':
                new_name = filepath + extension
                
                if dry_run:
                    print(f"[模拟] 重命名: {filepath} -> {new_name}")
                else:
                    try:
                        os.rename(filepath, new_name)
                        print(f"重命名: {filepath} -> {new_name}")
                    except OSError as e:
                        print(f"错误: 无法重命名 {filepath} - {e}")
                        continue
                
                count += 1
    
    print("-" * 50)
    action = "找到" if dry_run else "重命名"
    print(f"完成！共{action}了 {count} 个文件。")

def main():
    parser = argparse.ArgumentParser(description='给没有后缀的文件添加指定后缀')
    parser.add_argument('extension', nargs='?', default='.json', 
                       help='要添加的后缀（默认: .json）')
    parser.add_argument('--dry-run', action='store_true',
                       help='模拟运行，显示将要重命名的文件但不实际执行')
    
    args = parser.parse_args()
    
    add_extension_to_files(args.extension, args.dry_run)

if __name__ == "__main__":
    main()