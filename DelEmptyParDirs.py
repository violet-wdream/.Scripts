import os
import sys
import shutil

def collect_redundant_operations(root_dir):
    """
    递归遍历目录树，收集所有需要删除的冗余目录及其子目录的移动操作。

    冗余目录的定义：
    1. 不包含任何文件 (filenames is empty)。
    2. 只包含一个子目录 (len(dirnames) == 1)。
    3. 不是根目录本身。

    :param root_dir: 要处理的根目录路径。
    :return: 包含操作字典的列表。
    """
    if not os.path.isdir(root_dir):
        print(f"错误：路径 '{root_dir}' 不是一个有效目录。", file=sys.stderr)
        return []

    operations = []
    
    # 自底向上遍历，确保先处理深层目录
    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=False):
        
        # 1. 忽略根目录
        if os.path.abspath(dirpath) == os.path.abspath(root_dir):
            continue

        # 2. 如果有文件或多于一个子目录，则保留
        if filenames or len(dirnames) > 1:
            continue

        # 3. 只包含一个子目录
        if len(dirnames) == 1:
            
            sole_subdir_name = dirnames[0]
            
            # 要被提升的子目录的旧路径
            old_path = os.path.join(dirpath, sole_subdir_name)
            
            # 冗余目录的父目录
            parent_path = os.path.dirname(dirpath)
            
            # 子目录的新路径 (提升到父目录，保持原名)
            new_path = os.path.join(parent_path, sole_subdir_name)
            
            # 记录操作：(子目录的旧路径, 子目录的新路径, 要删除的冗余父目录)
            operations.append({
                'old_path': old_path, 
                'new_path': new_path, 
                'redundant_dir': dirpath
            })
            
    return operations


def execute_operations(operations):
    """
    执行收集到的目录移动和删除操作。

    :param operations: 包含操作字典的列表。
    """
    executed_count = 0
    
    for op in operations:
        old_path = op['old_path']
        new_path = op['new_path']
        redundant_dir = op['redundant_dir']
        
        # 检查目标路径是否已存在，防止覆盖数据
        if os.path.exists(new_path):
            print(f"[失败] 目标路径 '{os.path.relpath(new_path)}' 已存在。跳过。", file=sys.stderr)
            continue
        
        try:
            # 1. 移动/重命名子目录
            os.rename(old_path, new_path)
            
            # 2. 删除空的冗余父目录
            os.rmdir(redundant_dir)
            
            print(f"[成功] 提升: '{os.path.relpath(old_path)}' -> '{os.path.relpath(new_path)}'")
            print(f"         删除: '{os.path.relpath(redundant_dir)}'")
            executed_count += 1
            
        except OSError as e:
            # 捕捉权限、文件占用或目标路径非空的错误
            print(f"[失败] 无法处理 '{os.path.relpath(redundant_dir)}'。错误：{e}", file=sys.stderr)

    return executed_count


def main():
    # 自动确定根目录
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        root_dir = os.getcwd() 
    
    root_dir = os.path.abspath(root_dir)

    if not os.path.isdir(root_dir):
        print(f"错误：指定的路径 '{root_dir}' 不是一个有效目录。")
        sys.exit(1)

    print(f"--- 正在分析根目录: {root_dir} ---")
    
    run_count = 0
    
    # 循环清理多层嵌套的冗余目录，直到不再发现操作
    while True:
        run_count += 1
        operations = collect_redundant_operations(root_dir)

        if not operations:
            break
        
        # 仅在第一轮才打印详细列表和要求用户确认
        if run_count == 1:
            print("\n--- ⚠️ 发现以下冗余目录，即将执行操作：---")
            for i, op in enumerate(operations):
                print(f"[{i+1}] 冗余父目录 (待删除): {os.path.relpath(op['redundant_dir'], root_dir)}")
                print(f"      子目录 (待提升): {os.path.relpath(op['old_path'], root_dir)}")
                print(f"      目标新路径:      {os.path.relpath(op['new_path'], root_dir)}\n")
            
            print(f"总共有 {len(operations)} 个操作将在第一轮中被执行。")
            user_input = input("请确认是否执行这些操作？ (输入 'yes' 或 'y' 继续): ").strip().lower()

            if user_input not in ('yes', 'y'):
                print("用户取消操作。脚本退出。")
                return

        print(f"\n--- 正在执行实际操作 (第 {run_count} 轮) ---")
        
        executed_count = execute_operations(operations)
        
        if executed_count == 0 and run_count > 1:
            # 如果在后续轮次中没有执行任何操作，通常是因为目标路径冲突等错误，退出循环
            break
            
    print(f"\n--- 所有冗余目录清理完成。共运行 {run_count} 轮。---")


if __name__ == "__main__":
    main()