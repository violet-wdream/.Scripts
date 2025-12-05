import os
from PIL import Image

def merge_alpha_images(root):
    for dirpath, dirnames, filenames in os.walk(root):
        # 只处理以 _alpha.png 结尾的文件
        alpha_files = [f for f in filenames if f.endswith("_alpha.png")]

        for alpha_name in alpha_files:
            base_name = alpha_name.replace("_alpha.png", ".png")
            alpha_path = os.path.join(dirpath, alpha_name)
            base_path = os.path.join(dirpath, base_name)

            if not os.path.exists(base_path):
                print(f"缺少对应主图: {base_path}")
                continue

            try:
                base_img = Image.open(base_path).convert("RGBA")
                alpha_img = Image.open(alpha_path).convert("L")

                if base_img.size != alpha_img.size:
                    print(f"尺寸不一致，跳过: {base_path}")
                    continue

                # 使用 alpha 替换原图的透明度通道
                r, g, b, _ = base_img.split()
                merged = Image.merge("RGBA", (r, g, b, alpha_img))

                merged.save(base_path)
                print(f"合并完成 -> {base_path}")

                os.remove(alpha_path)
                print(f"删除 alpha 图片 -> {alpha_path}")

            except Exception as e:
                print(f"失败: {alpha_path} -> {e}")

# 调用
merge_alpha_images(os.getcwd())
