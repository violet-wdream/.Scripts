import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox

tapbody_keys = ["mail", "touch_body", "touch_drag"]
tapspecial_keys = ["complete", "home", "login", "mission", "mission_complete"] # 新增特殊动作键
taphead_keys = ["wedding", "touch_head", "touch_idle"]

def collect_files(root_dir):
    """
    遍历指定目录，收集所有符合 Live2D 模型结构的文件路径。
    结构要求: [模型名]/[模型名].model3.json 和 [模型名]/motions/
    """
    files_to_process = []
    for name in os.listdir(root_dir):
        model_dir = os.path.join(root_dir, name)
        if not os.path.isdir(model_dir):
            continue
        model_path = os.path.join(model_dir, f"{name}.model3.json")
        motions_dir = os.path.join(model_dir, "motions")
        # 确保模型文件和 motions 目录都存在
        if os.path.exists(model_path) and os.path.exists(motions_dir):
            files_to_process.append(model_path)
    return files_to_process

def shorten_path(path, levels=2):
    """
    路径缩短函数，仅保留最后 N 级目录，用于在列表中展示。
    """
    parts = path.replace("\\", "/").split("/")
    return "/".join(parts[-levels:])

def process_models(files_to_process):
    """
    遍历文件列表，读取 model3.json，分类 motions 目录下的动作文件，并更新 model3.json。
    """
    updated_files = 0
    for model_path in files_to_process:
        model_dir = os.path.dirname(model_path)
        name = os.path.basename(model_dir)
        motions_dir = os.path.join(model_dir, "motions")
        motion_files = [f for f in os.listdir(motions_dir) if f.endswith(".motion3.json")]

        # --- 动作列表初始化 ---
        tapbody_list, tapspecial_list, taphead_list = [], [], []

        # 遍历动作文件并分类
        for file in motion_files:
            base = file.replace(".motion3.json", "")
            
            # 检查是否属于 TapBody
            if any(base == k or base.startswith(f"{k}_") for k in tapbody_keys):
                tapbody_list.append({"Name": base, "File": f"motions/{file}"})
            
            # 检查是否属于 TapSpecial
            elif any(base == k or base.startswith(f"{k}_") for k in tapspecial_keys):
                tapspecial_list.append({"Name": base, "File": f"motions/{file}"})
            
            # 检查是否属于 TapHead
            elif any(base == k or base.startswith(f"{k}_") for k in taphead_keys):
                taphead_list.append({"Name": base, "File": f"motions/{file}"})

        # 读取旧的 model3.json 数据
        try:
            with open(model_path, "r", encoding="utf-8") as f:
                old_data = json.load(f)
        except json.JSONDecodeError as e:
            messagebox.showerror("错误", f"解析 JSON 文件失败: {model_path}\n错误信息: {e}")
            continue
        except FileNotFoundError:
            continue

        # 提取旧数据中的核心引用信息
        file_refs = old_data.get("FileReferences", {})
        moc = file_refs.get("Moc", "")
        textures = file_refs.get("Textures", [])
        physics = file_refs.get("Physics", "")
        model_name = old_data.get("Name", name)

        # 构建新的 model3.json 结构
        new_data = {
            "Version": 3,
            "Name": model_name,
            "FileReferences": {
                "Moc": moc,
                "Textures": textures,
                "Physics": physics,
                "Motions": {
                    # 保留原有的 Idle 动作（假设文件存在）
                    "Idle": [{"Name": "idle", "File": "motions/idle.motion3.json"}] if os.path.exists(os.path.join(motions_dir, "idle.motion3.json")) else [],
                    # 使用分类后的列表
                    "TapBody": tapbody_list,
                    "TapSpecial": tapspecial_list, # 写入新的特殊动作列表
                    "TapHead": taphead_list
                }
            },
            # 保持 HitAreas 不变 (假设 TouchSpecial/TapSpecial 逻辑不变)
            "HitAreas": [
                {"Name": "Body", "Id": "TouchBody", "Order": 2, "Motion": "TapBody"},
                {"Name": "Special", "Id": "TouchSpecial", "Order": 3, "Motion": "TapSpecial"},
                {"Name": "Head", "Id": "TouchHead", "Order": 1, "Motion": "TapHead"}
            ],
            # 保持 Groups 不变
            "Groups": [
                {"Target": "Parameter", "Name": "EyeBlink", "Ids": ["ParamEyeLOpen", "ParamEyeROpen"]},
                {"Target": "Parameter", "Name": "LipSync", "Ids": ["ParamMouthOpenY"]}
            ]
        }
        
        # 写入新的 model3.json 文件
        try:
            with open(model_path, "w", encoding="utf-8") as f:
                # 使用 indent=2 格式化，确保 ensure_ascii=False 允许写入中文
                json.dump(new_data, f, indent=2, ensure_ascii=False)
            updated_files += 1
        except Exception as e:
            messagebox.showerror("写入错误", f"写入文件失败: {model_path}\n错误信息: {e}")


    messagebox.showinfo("完成 🎉", f"处理完成，共更新 {updated_files} 个 model3.json 文件。")

def show_confirmation_dialog(parent, file_list):
    """
    自定义确认对话框，用于显示带有滚动条的文件列表。
    """
    dialog = tk.Toplevel(parent)
    dialog.title("确认处理以下文件？")
    dialog.geometry("500x400")
    dialog.transient(parent) # 设置为对主窗口模态
    dialog.grab_set() # 捕获所有事件，使其成为模态对话框
    
    # 使用一个属性来存储对话框结果
    dialog.result = False

    # 标题标签
    tk.Label(dialog, text=f"即将更新以下 {len(file_list)} 个文件：", 
             font=("Helvetica", 10, "bold"), anchor="w").pack(pady=10, padx=20, fill="x")

    # 滚动文本区域 (Scrollable Text Area)
    frame = tk.Frame(dialog, padx=20, pady=5)
    frame.pack(fill="both", expand=True)

    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side="right", fill="y")

    # wrap="none" 禁用自动换行
    text_area = tk.Text(frame, wrap="none", yscrollcommand=scrollbar.set, height=15, 
                        font=("Consolas", 9), relief="sunken", borderwidth=1)
    
    text_area.insert(tk.END, "\n".join(file_list))
    text_area.config(state="disabled") # 设为只读
    text_area.pack(side="left", fill="both", expand=True)

    scrollbar.config(command=text_area.yview)

    # 按钮处理函数
    def on_ok():
        dialog.result = True
        dialog.destroy()

    def on_cancel():
        dialog.result = False
        dialog.destroy()
        
    # 按钮框架
    btn_frame = tk.Frame(dialog)
    btn_frame.pack(pady=15)

    tk.Button(btn_frame, text="确认处理", command=on_ok, width=15, bg="#4CAF50", fg="white", activebackground="#45a049").pack(side="left", padx=15)
    tk.Button(btn_frame, text="取消", command=on_cancel, width=15, bg="#f44336", fg="white", activebackground="#d32f2f").pack(side="left", padx=15)

    # 等待对话框关闭
    parent.wait_window(dialog)
    return dialog.result

def select_folder():
    """
    用户选择目录，收集文件，并调用自定义确认对话框。
    """
    folder_selected = filedialog.askdirectory(title="选择模型文件目录的上一级目录")
    if not folder_selected:
        return

    files_to_process = collect_files(folder_selected)
    if not files_to_process:
        messagebox.showinfo("提示", "未找到可处理的 model3.json 文件。\n请确保模型文件夹结构为：\n[父目录]/[模型名]/[模型名].model3.json\n[父目录]/[模型名]/motions/*.motion3.json")
        return

    # 仅显示最后两级路径
    short_list = [shorten_path(p) for p in files_to_process]
    
    # 调用带滚动条的自定义对话框进行确认
    confirm = show_confirmation_dialog(root, short_list)
    
    if confirm:
        process_models(files_to_process)

# GUI 主程序
root = tk.Tk()
root.title("Model3 批量动作分类工具")
# 隐藏主窗口，因为用户通常只需要与对话框交互
# root.withdraw() 
# 或者保持主窗口可见，但使其简洁
root.geometry("400x150")
root.resizable(False, False)

# 确保主窗口的图标和样式一致（仅示例）
# try:
#     root.iconbitmap("icon.ico")
# except:
#     pass

btn = tk.Button(root, text="选择目录并处理", command=select_folder, width=30, height=1, font=("Helvetica", 12, "bold"), bg="#1E88E5", fg="white", relief="raised", bd=3)
btn.pack(pady=40, padx=20)

tk.Label(root, text="请选择包含所有 Live2D 模型子目录的父目录", font=("Helvetica", 9), fg="gray").pack()

root.mainloop()