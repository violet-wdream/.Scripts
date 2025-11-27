import os
import shutil
from pathlib import Path

def extract_contents(root_dir):
    root_path = Path(root_dir)
    if not root_path.is_dir():
        print(f"错误：{root_dir} 不是一个有效的目录")
        return

    # 遍历根目录下的一级子目录
    for item in root_path.iterdir():
        if not item.is_dir():
            continue  # 跳过根目录下的文件

        subdir = item
        print(f"\n正在处理目录: {subdir.name}")

        # 检查是否包含子文件夹
        has_subfolder = any(p.is_dir() for p in subdir.iterdir())

        if not has_subfolder:
            print(f"  → 纯文件目录，跳过: {subdir.name}")
            continue

        print(f"  → 包含子文件夹，开始提取内容...")

        # 递归提取所有内容到当前 subdir
        _move_all_contents_up(subdir)

        print(f"  → 提取完成: {subdir.name}")

def _move_all_contents_up(base_dir):
    """
    将 base_dir 下的所有子文件夹内容，逐级提升到 base_dir
    重复直到没有子文件夹为止
    """
    while True:
        subfolders = [p for p in base_dir.iterdir() if p.is_dir()]
        if not subfolders:
            break

        for folder in subfolders:
            for item in folder.iterdir():
                dest = base_dir / item.name

                # 处理文件名冲突
                if dest.exists():
                    base_name = item.stem if item.suffix else item.name
                    suffix = item.suffix
                    counter = 1
                    while dest.exists():
                        new_name = f"{base_name}_{counter}{suffix}"
                        dest = base_dir / new_name
                        counter += 1

                shutil.move(str(item), str(dest))

            # 删除空的原文件夹
            try:
                folder.rmdir()
                print(f"    删除空文件夹: {folder.name}")
            except OSError as e:
                print(f"    无法删除文件夹 {folder.name}: {e}")

if __name__ == "__main__":
    # === 修改这里为你的根目录路径 ===
    ROOT_DIRECTORY = "."  # 当前目录，或写绝对路径如 r"D:\mydata"

    print(f"开始处理根目录: {os.path.abspath(ROOT_DIRECTORY)}")
    extract_contents(ROOT_DIRECTORY)
    print("\n所有操作完成！")