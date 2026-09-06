import json
import shutil
from pathlib import Path

INPUT_PATH = Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\resources\output")
# 可以处理 cocos 导出的压缩结构，提取出 skeletonJson 并覆盖原文件
# [
#   1,
#   ["b6Yj40aflHoZ8bNfzLUE6v@6c48a"],
#   0,
#   [ # data[3]
#     [ # data[3][0]
#       "sp.SkeletonData",
#       ["_name", "_atlasText", "textureNames", "_skeletonJson", "textures"], # data[3][0][1]
#       -1,
#       3
#     ]
#   ],
#   [[0, 0, 1, 2, 3, 4, 5]],
#   [ #block - data[5]
#     [# entry - block[0]
#       0,
#       "interactBg_0015", # _name
#       "\r\ninteractBg_0015.png\r\nsize: 1927,1927\r\n...", # _atlasText
#       ["interactBg_0015.png"], # textureNames
#       {
#         ...# _skeletonJson
#       },
#       [0]
#     ]
#   ],
#   0,
#   0,
#   [0],
#   [-1],
#   [0]
# ]

def extract(data):
    try:
        fields = data[3][0][1]
        entry = data[5][0]

        values = dict(zip(fields, entry[1:]))

        return (
            values.get("_name"),
            values.get("_native"),
            values.get("_atlasText"),
            values.get("textureNames"),
            values.get("_skeletonJson"),
        )

    except (IndexError, TypeError, KeyError):
        return None


def process_file(p: Path):
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return

    result = extract(data)
    if not result:
        return

    name, native, atlas, textures, skeleton = result
    name = name or p.stem

    # 1. 提取 Atlas
    if atlas:
        atlas_path = p.with_name(f"{name}.atlas")
        atlas = atlas.replace("\r\n", "\n").replace("\r", "\n")
        atlas_path.write_text(
            atlas,
            encoding="utf-8",
            newline="\r\n"
        )
        print(f"[ATLAS] {atlas_path}")

    # 2. 已经存在 Skeleton JSON
    if isinstance(skeleton, dict):
        json_path = p.with_name(f"{name}.skel.json")
        json_path.write_text(
            json.dumps(
                skeleton,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )
        print(f"[JSON]  {json_path}")

    # 3. _native = .bin，复制成 .skel
    elif native:
        bin_path = p.with_suffix(native)

        if bin_path.exists():
            skel_path = p.with_name(f"{name}.skel")
            shutil.copy2(bin_path, skel_path)
            print(f"[SKEL]  {skel_path}")
        else:
            print(f"[WARN] 找不到 {bin_path}")


def main():
    for p in INPUT_PATH.rglob("*.json"):
        process_file(p)


if __name__ == "__main__":
    main()