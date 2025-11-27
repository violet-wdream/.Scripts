import os

def delete_files_with_extensions(extensions):
    """
    批量删除当前目录及子目录中指定后缀的文件（带确认）
    :param extensions: list[str]  要删除的文件后缀，例如 ['.pvr.ccz', '.meta']
    """
    current_dir = os.getcwd()
    print(f"扫描目录: {current_dir}\n")

    # 记录所有待删除的文件
    targets = []

    for dirpath, dirnames, filenames in os.walk(current_dir):
        for file in filenames:
            if any(file.lower().endswith(ext.lower()) for ext in extensions):
                targets.append(os.path.join(dirpath, file))

    if not targets:
        print("✅ 没有找到匹配的文件。")
        return

    # 显示待删除文件列表
    print("以下文件将被删除：\n")
    for path in targets:
        print(" -", path)

    print(f"\n共 {len(targets)} 个文件。")
    confirm = input("\n❓是否确认删除这些文件？(y/N)：").strip().lower()

    if confirm != 'y':
        print("🚫 已取消操作。")
        return

    # 执行删除
    deleted_count = 0
    for file_path in targets:
        try:
            os.remove(file_path)
            deleted_count += 1
            print(f"🗑️ 已删除: {file_path}")
        except Exception as e:
            print(f"⚠删除失败 {file_path}: {e}")

    print(f"\n✅ 删除完成！共删除 {deleted_count} 个文件。")

# ===== 配置要删除的文件后缀 =====
extensions_to_delete = [
    '.pvr.ccz',
    '.meta',
    '.bak',
    '.tmp'
]

delete_files_with_extensions(extensions_to_delete)
