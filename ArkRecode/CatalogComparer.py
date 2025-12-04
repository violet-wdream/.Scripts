import json
import os
import sys
from datetime import datetime

# 需要匹配的前缀
OLD_PREFIXES = [
    "http://PatchDomain/Android/defaultlocalgroup_assets_assets/game/hero/",
    "http://PatchDomain/Android/defaultlocalgroup_assets_assets/game/cg/",
    "http://PatchDomain/Android/firstbundlegroup_assets_assets/game/hero/",
    "http://PatchDomain/Android/firstbundlegroup_assets_assets/game/cg/"
]

# 输出使用的新前缀
NEW_BASE = "https://patch-arkre-nu.ecchi.xxx/GamePatch/Android/"


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_core(url: str) -> str:
    """返回用于比较的主体路径（去掉 hash + .bundle）"""
    return url.rsplit("_", 1)[0]


def replace_prefix(url: str) -> str:
    """
    输出用：把旧前缀替换为 New Base。
    例如：
    http://PatchDomain/Android/defaultlocalgroup_assets_assets/xxx
    =>
    https://patch-arkre-nu.ecchi.xxx/GamePatch/Android/defaultlocalgroup_assets_assets/xxx
    """
    for old_prefix in OLD_PREFIXES:
        if url.startswith(old_prefix):
            suffix = url[len("http://PatchDomain/Android/"):]  # 去掉旧前缀的头部部分
            return NEW_BASE + suffix
    return url  # 不匹配的直接返回


def filter_full_and_core(data):
    """
    返回完整 URL 列表（只保留指定前缀）和主体路径集合（用于比较）
    """
    ids = data.get("m_InternalIds", [])
    full_urls = []
    core_set = set()

    for url in ids:
        for prefix in OLD_PREFIXES:
            if url.startswith(prefix):
                full_urls.append(url)
                core_set.add(extract_core(url))
                break

    return full_urls, core_set


def main(old_file, new_file):
    old_json = load_json(old_file)
    new_json = load_json(new_file)

    old_full, old_core = filter_full_and_core(old_json)
    new_full, new_core = filter_full_and_core(new_json)

    added_core = new_core - old_core

    if not added_core:
        print("没有新增内容")
        return

    # 输出完整 new.json URL，但替换前缀
    added_full = sorted([
        replace_prefix(url)
        for url in new_full
        if extract_core(url) in added_core
    ])

    date_str = datetime.now().strftime("%Y.%m.%d")
    out_file = f"catalog-update-{date_str}.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"added": added_full}, f, ensure_ascii=False, indent=4)

    print("新增内容已写入:", out_file)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: python compare_catalog.py old.json new.json")
        sys.exit(1)

    old_file = sys.argv[1]
    new_file = sys.argv[2]

    if not os.path.exists(old_file):
        print("旧文件不存在:", old_file)
        sys.exit(1)

    if not os.path.exists(new_file):
        print("新文件不存在:", new_file)
        sys.exit(1)

    main(old_file, new_file)
