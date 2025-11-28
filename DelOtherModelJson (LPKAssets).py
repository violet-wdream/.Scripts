import os
import re

def clean_model_json_files_with_confirmation():
    """
    搜索当前目录下的所有子目录，根据 atlases_0_atlas_NUM 文件保留对应的 modelNUM.json，
    并删除该子目录下其他 model*.json 文件。操作前需要用户输入 'yes' 确认。
    """
    
    # 获取脚本所在的当前目录
    base_dir = os.path.abspath(os.path.dirname(__file__))
    print(f"📂 正在搜索主目录下的子目录: {base_dir}")

    sub_dirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    
    if not sub_dirs:
        print("🔍 当前目录下没有找到子目录，任务结束。")
        return

    # 正则表达式用于匹配 atlases_0_atlas_NUM 文件，并捕获其中的数字 (NUM)
    atlas_pattern = re.compile(r"atlases_0_atlas_(\d+)$")
    # 正则表达式用于匹配 modelNUM.json 文件，并捕获其中的数字 (NUM)
    model_pattern = re.compile(r"model(\d+)\.json$", re.IGNORECASE)

    # 存储所有待删除文件的列表 [(文件路径, 目录名, 文件名)]
    files_to_delete = []

    # --- 阶段一：扫描文件并生成待删除清单 ---
    for subdir_name in sub_dirs:
        current_dir = os.path.join(base_dir, subdir_name)
        
        # 1. 扫描 atlases 文件，收集需要保留的 NUM 值
        files_in_subdir = os.listdir(current_dir)
        retained_nums = set()
        
        for filename in files_in_subdir:
            match = atlas_pattern.match(filename)
            if match:
                num_str = match.group(1)
                retained_nums.add(num_str)

        if not retained_nums:
            continue  # 如果目录中没有 atlases 文件，则跳过

        # 2. 遍历所有 model*.json 文件，识别待删除文件
        for filename in files_in_subdir:
            model_match = model_pattern.match(filename)
            
            if model_match:
                model_num = model_match.group(1)
                
                # 如果 model 文件中的 NUM 不在需要保留的集合中，则标记为待删除
                if model_num not in retained_nums:
                    file_path = os.path.join(current_dir, filename)
                    files_to_delete.append((file_path, subdir_name, filename))

    # --- 阶段二：用户确认和执行删除操作 ---
    
    if not files_to_delete:
        print("\n🎉 扫描完成，没有发现需要删除的 model*.json 文件。")
        return

    print("\n--- 待删除文件清单 ---")
    print(f"找到 {len(files_to_delete)} 个 model*.json 文件将被删除:")
    print("-------------------------")
    for i, (path, subdir, filename) in enumerate(files_to_delete, 1):
        print(f"{i}. [{subdir}] {filename}")
    print("-------------------------")

    # 提示用户进行确认
    confirmation = input(
        f"\n❓ 请确认是否执行文件删除操作 (一旦删除，文件将难以恢复)。\n"
        f"输入 'yes' 继续执行，输入其他任意内容取消: "
    ).strip().lower()

    if confirmation == 'yes':
        deleted_count = 0
        print("\n--- 开始执行删除操作 ---")
        
        for file_path, _, filename in files_to_delete:
            try:
                os.remove(file_path)
                print(f"🗑️ 已删除: {file_path}")
                deleted_count += 1
            except Exception as e:
                print(f"❌ 删除文件 {filename} 失败: {e}")

        print("\n--- 任务完成 ---")
        print(f"🎉 成功删除了 {deleted_count} 个多余的 model*.json 文件。")

    else:
        print("\n🚫 用户取消了操作。文件未被删除，原文件保留。")


# --- 脚本执行入口 ---
if __name__ == "__main__":
    clean_model_json_files_with_confirmation()