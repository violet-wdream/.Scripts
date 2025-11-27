import os
import json
import sys
from pathlib import Path
from typing import List, Dict

# --- 配置常量 ---
TARGET_DAT_FILE = "character.dat"
TARGET_JSON_PATTERN = "MOC.*.json"

def collect_operations(root_dir: Path) -> List[Dict]:
    """
    遍历目录，收集需要执行的重命名和 JSON 修改操作。
    
    :param root_dir: 搜索的根目录。
    :return: 包含操作字典的列表。
    """
    operations = []
    
    # 遍历当前目录下的所有子目录
    for subdir in root_dir.iterdir():
        if not subdir.is_dir():
            continue
        
        # 1. 检查是否存在 character.dat
        dat_path = subdir / TARGET_DAT_FILE
        if not dat_path.exists():
            continue

        # 2. 检查是否存在匹配的 MOC JSON 文件
        # 使用 glob 查找 MOC.*.json 文件
        moc_json_files = list(subdir.glob(TARGET_JSON_PATTERN))
        
        if not moc_json_files:
            # 找到 character.dat 但没有找到对应的 JSON 配置
            print(f"警告: 目录 {subdir.name} 包含 {TARGET_DAT_FILE}，但未找到匹配 {TARGET_JSON_PATTERN} 的 JSON 文件。跳过此目录。", file=sys.stderr)
            continue
            
        # 假设我们只处理找到的第一个匹配文件
        old_json_path = moc_json_files[0]
        
        # 3. 定义新的文件名 (使用目录名作为基础 name)
        name = subdir.name
        
        new_dat_path = subdir / f"{name}.moc"
        new_json_path = subdir / f"{name}.model.json"
        
        # 4. 记录操作
        operations.append({
            "name": name,
            "directory": subdir,
            "dat_rename": (dat_path, new_dat_path),
            "json_rename": (old_json_path, new_json_path),
            "new_model_value": f"{name}.moc" # JSON 文件中 model 键的新值
        })

    return operations


def execute_operations(operations: List[Dict]):
    """
    执行文件重命名和 JSON 内容修改操作。
    """
    executed_count = 0
    
    for op in operations:
        name = op["name"]
        old_dat, new_dat = op["dat_rename"]
        old_json, new_json = op["json_rename"]
        new_model_value = op["new_model_value"]
        
        print(f"\n--- 正在处理: {name} ---")
        
        try:
            # --- A. 修改 JSON 文件内容 ---
            print(f" 1. 正在读取和更新 JSON 内容...")
            
            # 读取旧 JSON 内容
            with open(old_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 检查并更新 model 键
            if data.get("model") != new_model_value:
                old_model_value = data.get("model", "N/A")
                data["model"] = new_model_value
                
                # 写回 JSON 文件
                with open(old_json, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                print(f"    - JSON 'model' 键已更新: '{old_model_value}' -> '{new_model_value}'")
            else:
                 print(f"    - JSON 'model' 键已是最新值: '{new_model_value}'")
            
            # --- B. 重命名 character.dat 为 name.moc ---
            print(f" 2. 正在重命名 {old_dat.name} -> {new_dat.name}...")
            old_dat.rename(new_dat)
            print("    - 重命名成功。")

            # --- C. 重命名 MOC.*.json 为 name.model.json ---
            print(f" 3. 正在重命名 {old_json.name} -> {new_json.name}...")
            old_json.rename(new_json)
            print("    - 重命名成功。")
            
            executed_count += 1
            
        except Exception as e:
            print(f"\n[错误] 处理目录 {name} 失败: {e}", file=sys.stderr)
            print("请检查文件权限或文件是否被其他程序占用。")

    print(f"\n--- 全部处理完成。共成功更新 {executed_count} 个模型目录。---")


def main():
    root_dir = Path(os.getcwd())
    print(f"--- 脚本启动：正在搜索目录 '{root_dir}' ---")
    
    operations = collect_operations(root_dir)

    if not operations:
        print("\n未找到符合条件 (目录名/包含 character.dat/包含 MOC.*.json) 的模型目录。")
        return

    # 1. 打印操作列表
    print("\n--- ⚠️ 发现以下模型目录，即将执行文件和内容修改操作：---")
    
    for i, op in enumerate(operations):
        old_json_name = op["json_rename"][0].name
        new_json_name = op["json_rename"][1].name
        
        print(f"[{i+1}] 目录: {op['name']}")
        print(f"    - 文件重命名 1: {op['dat_rename'][0].name} -> {op['dat_rename'][1].name}")
        print(f"    - 文件重命名 2: {old_json_name} -> {new_json_name}")
        print(f"    - JSON 内容修改: 'model' 键值将设为 '{op['new_model_value']}'")

    # 2. 征求用户确认
    print(f"\n总共有 {len(operations)} 个目录将被处理。")
    user_input = input("请确认是否执行这些操作？ (输入 'yes' 或 'y' 继续): ").strip().lower()

    # 3. 执行或退出
    if user_input in ('yes', 'y'):
        execute_operations(operations)
    else:
        print("用户取消操作。脚本退出。")

if __name__ == "__main__":
    main()