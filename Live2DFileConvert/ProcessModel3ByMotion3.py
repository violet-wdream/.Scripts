import os
import json
import glob
from pathlib import Path

def main():
    print("开始查找 Live2D 模型...")

    # 使用 Path 更简洁地遍历所有 .moc3 文件
    moc3_files = list(Path('.').rglob('*.moc3'))
    if not moc3_files:
        print("未找到任何 .moc3 文件")
        return

    print(f"找到 {len(moc3_files)} 个 Live2D 模型")
    processed = set()

    for moc3_path in moc3_files:
        model_dir = moc3_path.parent
        if model_dir in processed:
            continue

        print(f"\n处理模型: {model_dir}")

        # 1. 处理 motions 目录：自动添加 .json 后缀
        motions_dir = model_dir / 'motions'
        if not motions_dir.exists():
            print("  未找到 motions 目录，跳过")
            continue

        motion_files = []
        for motion_path in motions_dir.glob('*.motion3'):
            new_path = motion_path.with_suffix('.motion3.json')
            if not new_path.exists():
                try:
                    motion_path.rename(new_path)
                    print(f"  重命名: {motion_path.name} → {new_path.name}")
                except Exception as e:
                    print(f"  重命名失败 {motion_path.name}: {e}")
            motion_files.append(new_path.name)

        # 包含已存在的 .motion3.json
        motion_files.extend([p.name for p in motions_dir.glob('*.motion3.json')])
        motion_files = sorted(set(motion_files))  # 去重排序

        if not motion_files:
            print("  未找到任何 .motion3.json 动作文件")
            continue

        print(f"  发现 {len(motion_files)} 个动作:")
        for f in motion_files[:10]:  # 只显示前10个，避免刷屏
            print(f"    - {f}")
        if len(motion_files) > 10:
            print(f"    ... 共 {len(motion_files)} 个")

        # 2. 获取模型名称
        model_name = moc3_path.stem

        # 3. 自动收集资源
        textures = [f"textures/{p.name}" for p in (model_dir / 'textures').glob('*.png')] if (model_dir / 'textures').exists() else []
        physics_path = model_dir / f"{model_name}.physics3.json"
        physics = f"{model_name}.physics3.json" if physics_path.exists() else None

        # 4. 构建 Motions 结构
        motions_data = {
            f.removesuffix('.motion3.json').removesuffix('.json'): [{"File": f"motions/{f}"}]
            for f in motion_files
        }

        # 5. 读取或创建 .model3.json
        model_json_path = model_dir / f"{model_name}.model3.json"
        if model_json_path.exists():
            with open(model_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"  更新现有 {model_json_path.name}")
        else:
            print(f"  创建新的 {model_json_path.name}")
            data = {
                "Version": 3,
                "Name": model_name,
                "FileReferences": {
                    "Moc": f"{model_name}.moc3",
                    "Textures": textures,
                    "Physics": physics,
                    "Pose": None,
                    "DisplayInfo": None,
                    "Motions": {},
                    "Expressions": []
                },
                "Groups": [
                    {"Target": "Parameter", "Name": "EyeBlink", "Ids": ["ParamEyeROpen", "ParamEyeLOpen"]},
                    {"Target": "Parameter", "Name": "LipSync", "Ids": ["ParamMouthForm", "ParamMouthOpenY"]}
                ]
            }

        # 强制更新 Motions（保留其他自定义内容）
        data.setdefault("FileReferences", {})["Motions"] = motions_data

        # 6. 写回文件（美化 JSON）
        try:
            with open(model_json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  已保存: {model_json_path.name}")
            print(f"  更新动作组: {', '.join(motions_data.keys())}")
        except Exception as e:
            print(f"  保存失败: {e}")

        processed.add(model_dir)

    print(f"\n完成！共处理 {len(processed)} 个模型")

if __name__ == "__main__":
    main()