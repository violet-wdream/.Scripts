import os
import re
from PIL import Image

def resize_image_nearest(image_path, new_size, output_path):
    image = Image.open(image_path)
    resized_image = image.resize(new_size, Image.NEAREST)
    resized_image.save(output_path)


spine_folder = os.getcwd()
atlas_files = []

for root, dirs, files in os.walk(spine_folder):
    for file in files:
        if file.endswith(".atlas"):
            atlas_files.append(os.path.join(root, file))

for atlas_file in atlas_files:
    with open(atlas_file, "r",encoding="utf-8") as file:
        lines = file.readlines()

    current_image = None
    correct_size = None

    image_pattern = re.compile(r'([^#]+)\.png')
    size_pattern = re.compile(r'size:\s*(\d+),\s*(\d+)')

    for line in lines:
        image_match = image_pattern.search(line)
        size_match = size_pattern.search(line)

        if image_match:
            current_image = image_match.group(1) + ".png"
        elif size_match:
            width, height = map(int, size_match.groups())
            correct_size = (width, height)
            if current_image and correct_size:
                image_path = os.path.join(os.path.dirname(atlas_file), current_image)
                if os.path.exists(image_path) and Image.open(image_path).size != correct_size:
                    print(f"缩放 {image_path} 到 {correct_size} ")
                    resize_image_nearest(image_path, correct_size, image_path)
                current_image = None
                correct_size = None