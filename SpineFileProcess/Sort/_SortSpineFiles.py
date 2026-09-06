from pathlib import Path
import json
from SpineFileProcess.Atlas_process import deserialize_atlas
import subprocess

converter_exe = Path(
    r"D:\Games\GameUnpackAssets\mymodel\.Scripts\SpineFileProcess\Converter\SpineSkeletonDataConverter.exe"
)
def convert_skel_to_json(skel_path: Path, json_path: Path):
    if not converter_exe.exists():
        raise FileNotFoundError(f"SpineSkeletonDataConverter.exe not found: {converter_exe}")

    cmd = [str(converter_exe), str(skel_path), str(json_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Failed to convert {skel_path} to {json_path}: {result.stderr}")

    print(f"Converted {skel_path} to {json_path}")


class SpineModel:
    def __init__(self, image_paths: list[Path], atlas_path: Path, skel_path: Path):
        self.image_paths = image_paths
        self.atlas_path = atlas_path
        self.skel_path = skel_path
    def show_info(self):
        print(f"SpineModel: images: {self.image_paths}\n"
              f"atlas: {self.atlas_path}\n"
              f"skel: {self.skel_path}\n")


def parse_atlas(file: Path) -> tuple[list[str], list[str]]:
    """" parse atlas file, return (image_names, region_names) """
    atlas_text = file.read_text(encoding="utf-8")
    if not "size:" in atlas_text:
        raise ValueError(f"Not a valid spine atlas file: {file}")

    atlas_info = deserialize_atlas(file.stem, atlas_text)
    images = atlas_info.get_page_names()
    regions = atlas_info.get_region_names()

    return images, regions


def extract_json_attachments(json_path: Path) -> list[str]:
    """ extract all names from json file """
    json_data = json_path.read_bytes()
    if not b'"skeleton":' in json_data:
        raise ValueError(f"Not a valid spine json file: {json_path}")

    json_obj = json.loads(json_data)
    if not "slots" in json_obj:
        raise ValueError(f"No slots found in spine json file: {json_path}")

    attachments = set()
    skins = json_obj.get("skins", {})

    for skin_name, skin_data in skins.items():
        for slot_name, slot_data in skin_data.items():
            if not isinstance(slot_data, dict):
                continue

            for attachment_name, attachment_data in slot_data.items():
                atype = attachment_data.get("type", "region")
                if atype not in ("region", "mesh", "linkedmesh"):
                    continue
                if isinstance(attachment_data, dict):
                    path = attachment_data.get("path") or attachment_name
                    # path = path.rsplit('/', 1)[-1]
                    attachments.add(path)

    return list(attachments)


def score_matching_rate(regions: list[str], attachments: list[str]) -> float:
    """ calculate the matching rate between regions and attachments """
    if not regions or not attachments:
        return 0.0
    # regions 总数不可能比 attachments 少
    if len(regions) < len(attachments):
        return 0.0
    for a in attachments:
        if a not in regions:
            return 0.0

    matched = sum(1 for r in attachments if r in regions)
    return matched / len(regions)

if __name__ == "__main__":
    # test parse_atlas
    all_atlas_paths = Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\DaoYou\test\atlas") # atlas
    all_image_paths = Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\DaoYou\test\png") # png/webp
    all_skel_paths = Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\DaoYou\test\skel") # skel/json
    out_path = Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\DaoYou\test\out") # output

    # atlas 根据 page 中名称匹配对应的图片, 同时根据第一张图片的名称重命名 atlas, 提取出所有 region 名称
    # 对于骨骼而言, 因为没有找到解析skel的库, 只能先转换为json, 提取 "slots" > "attachment"
    # attachment 中的名称就是 region 名称, 通过匹配率获取得分

    skel_attachments_dict: dict[Path, list[str]] = {}
    print(f"Processing skel/json files")
    for sk in all_skel_paths.rglob("*.json"):
        atts = extract_json_attachments(sk)
        skel_attachments_dict[sk] = atts

    for sk in all_skel_paths.rglob("*.skel"):
        tmp_path = out_path / (sk.stem + ".json")
        if not tmp_path.exists():
            convert_skel_to_json(sk, tmp_path)
        atts = extract_json_attachments(tmp_path)
        skel_attachments_dict[sk] = atts
        # 删除临时生成的json文件
        # tmp_path.unlink()

    print(f"Processing atlas files")
    for atlas in all_atlas_paths.rglob("*.atlas"):
        # print(f"Processing atlas: {atlas}")

        imgs, rgs = parse_atlas(atlas)
        # print(f"Parsed {atlas}: {len(imgs)} images, {len(rgs)} regions")
        img_paths = [all_image_paths / img for img in imgs]

        scores: dict[Path, float] = {}
        for sk, atts in skel_attachments_dict.items():
            rate = score_matching_rate(rgs, atts)
            scores[sk] = rate


        max_matched_skel = max(scores, key=scores.get)
        # if scores[max_matched_skel] > threshold:
        #     print(f"matching rate for {atlas}: {scores[max_matched_skel]:.2f}")
        # print(f"max matched skel for {atlas}: {max_matched_skel} with score {scores[max_matched_skel]:.2f}")
        sp = SpineModel(img_paths, atlas, max_matched_skel)
        if scores[max_matched_skel] < 0.6:
            # print(f"Warning: low matching rate for {atlas}: {scores[max_matched_skel]:.2f}")
            # print(f"Skel: {max_matched_skel}")
            pass