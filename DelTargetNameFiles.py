import os

def delete_targets_in_current_dir():
    root = os.getcwd()     # 当前目录
    targets = {"Mosaic.png", "CensorMask_alpha.png"}

    for dirpath, dirnames, filenames in os.walk(root):
        for filename in filenames:
            if filename in targets:
                full_path = os.path.join(dirpath, filename)
                try:
                    os.remove(full_path)
                    print(f"删除: {full_path}")
                except Exception as e:
                    print(f"失败: {full_path} -> {e}")

delete_targets_in_current_dir()
