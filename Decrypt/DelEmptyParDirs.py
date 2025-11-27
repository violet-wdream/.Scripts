import os
import sys
import shutil # <-- 新增

def collect_redundant_operations(root_dir):
    """
    递归遍历目录树，收集所有需要删除的冗余目录及其内容的移动/合并操作。
    :param root_dir: 要处理的根目录路径。
    :return: 包含操作字典的列表。
    """
    if not os.path.isdir(root_dir):
        print(f"错误：路径 '{root_dir}' 不是一个有效目录。", file=sys.stderr)
        return []

    operations = []
    
    # 递归遍历目录树（自底向上）
    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=False):
        
        # 1. 检查当前目录是否是根目录（不应该删除根目录本身）
        if os.path.abspath(dirpath) == os.path.abspath(root_dir):
            continue

        # 2. 如果有文件，或者有超过一个子目录，则保留当前目录
        if filenames or len(dirnames) > 1:
            continue

        # 3. 检查是否只包含一个子目录
        if len(dirnames) == 1:
            
            # 获取唯一的子目录名
            sole_subdir_name = dirnames[0]
            old_path = os.path.join(dirpath, sole_subdir_name)
            
            # 目标：将子目录的内容提升到 dirpath 的父目录。
            # new_path 是 dirpath 的父目录
            parent_path = os.path.dirname(dirpath)
            
            # --- 关键修正：new_path 应该是父目录本身！ ---
            # 我们要将 old_path (子目录) 提升到 parent_path (冗余目录的父目录)
            # 记录操作：(子目录的旧路径, 冗余父目录, 目标父目录)
            operations.append({
                'content_path': old_path,          # 待移动/合并的目录 (目录1/目录1/目录1)
                'redundant_dir': dirpath,          # 待删除的冗余父目录 (目录1/目录1)
                'target_parent': parent_path       # 目标父目录 (目录1)
            })
            
    return operations


def execute_operations(operations):
    """
    执行收集到的目录移动和删除操作。
    此版本使用 shutil.move 处理目录内容移动和合并。
    
    :param operations: 包含操作字典的列表。
    """
    executed_count = 0
    
    for op in operations:
        content_path = op['content_path']
        redundant_dir = op['redundant_dir']
        target_parent = op['target_parent']
        
        # 目标内容的新路径 (即 target_parent + 待移动目录的名字)
        content_name = os.path.basename(content_path)
        new_path = os.path.join(target_parent, content_name)
        
        # 记录提升操作 (用于打印)
        operation_type = "提升/移动"
        
        try:
            # 1. 检查目标位置是否已存在同名目录 (即同名合并的情况)
            if os.path.isdir(new_path):
                # 目标已存在，需要将内容移动到现有目录中
                # 遍历待移动目录的内容
                for item_name in os.listdir(content_path):
                    src_path = os.path.join(content_path, item_name)
                    dst_path = os.path.join(new_path, item_name)
                    
                    # 使用 shutil.move，它比 os.rename 更强大，
                    # 可以在不同分区之间移动，并且可以覆盖文件。
                    shutil.move(src_path, dst_path)
                
                # 移动完成后，待移动的目录 (content_path) 现在是空的
                # 因此，现在可以删除 content_path
                os.rmdir(content_path)
                operation_type = "内容合并"
                
            else:
                # 目标目录不存在，执行简单的重命名/移动
                # shutil.move(content_path, new_path)
                # 因为 content_path 是一个目录，shutil.move 会将其移动到 target_parent
                # 保持原名 content_name，效果就是 new_path
                shutil.move(content_path, target_parent) # 移动目录到其新的父目录
                
            
            # 2. 删除冗余父目录 (冗余目录现在应该是空的)
            # 注意: 如果 os.rmdir 失败 (目录不为空)，会抛出 OSError
            os.rmdir(redundant_dir)
            
            # 使用 os.path.relpath 打印相对路径，更简洁
            print(f"[{operation_type}] 成功: '{os.path.relpath(content_path)}' -> '{os.path.relpath(target_parent)}'")
            print(f"        删除冗余目录: '{os.path.relpath(redundant_dir)}'")
            executed_count += 1
            
        except OSError as e:
            # 捕捉权限、文件占用或目标路径已存在的错误
            # 主要是 rmdir 失败（目录不为空）或 shutil.move 失败
            print(f"[失败] 无法处理 '{os.path.relpath(redundant_dir)}' 提升操作。错误：{e}", file=sys.stderr)

    print(f"\n--- 执行完成。共成功处理 {executed_count} 个冗余目录。---")


def main():
    # --- 自动确定根目录 ---
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        root_dir = os.getcwd() 
    # -----------------------
    
    root_dir = os.path.abspath(root_dir)

    if not os.path.isdir(root_dir):
        print(f"错误：指定的路径 '{root_dir}' 不是一个有效目录。")
        sys.exit(1)

    print(f"--- 正在分析根目录: {root_dir} ---")
    operations = collect_redundant_operations(root_dir)

    if not operations:
        print("未发现任何需要删除的冗余父级目录。")
        return

    # 1. 打印操作列表
    print("\n--- ⚠️ 发现以下冗余目录，即将执行操作：---")
    # 打印时使用相对路径，更易读
    for i, op in enumerate(operations):
        # 目标新路径即 target_parent + content_name
        content_name = os.path.basename(op['content_path'])
        target_path = os.path.join(op['target_parent'], content_name)
        
        print(f"[{i+1}] 冗余父目录 (待删除): {os.path.relpath(op['redundant_dir'], root_dir)}")
        print(f"    子目录 (待提升): {os.path.relpath(op['content_path'], root_dir)}")
        print(f"    目标父目录 (内容将被提升到): {os.path.relpath(op['target_parent'], root_dir)}")
        # 提示用户如果目标路径存在同名目录，将进行内容合并
        print(f"    最终目标路径:       {os.path.relpath(target_path, root_dir)} (如果目标路径已存在同名目录，将合并内容)\n")
    
    # 2. 征求用户确认
    print(f"总共有 {len(operations)} 个操作将被执行。")
    user_input = input("请确认是否执行这些操作？ (输入 'yes' 或 'y' 继续): ").strip().lower()

    # 3. 执行或退出
    if user_input in ('yes', 'y'):
        print("\n--- 正在执行实际操作 (注意：目录合并操作无法撤销) ---")
        execute_operations(operations)
    else:
        print("用户取消操作。脚本退出。")

if __name__ == "__main__":
    main()