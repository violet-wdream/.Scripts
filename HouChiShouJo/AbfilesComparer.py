import sys
import time

BASE = "https://sf-snh5.bytedgame.com/obj/youai-c10-cdn-sg/gdl_app_302906/game/webgl/webgl-release/Desktop/common/"

def format_ts():
    return time.strftime("%Y.%m.%d.%H%M%S", time.localtime())

def load_common_dict(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = [x.strip() for x in f if x.strip()]

    try:
        idx = lines.index("common")
    except ValueError:
        return {}

    idx += 1
    total = int(lines[idx])
    idx += 1

    d = {}
    for i in range(total):
        row = lines[idx + i]
        parts = row.split("|")
        if len(parts) < 4:
            continue
        item1 = parts[0].strip()
        d[item1] = row

    return d


def extract_url(row):
    parts = row.split("|")
    item1 = parts[0].strip()
    item3 = parts[2].strip()
    return BASE + item3 + item1


if __name__ == "__main__":
    args = sys.argv[1:]

    if len(args) == 0:
        print("用法: python compare.py old.txt [new.txt]")
        sys.exit(1)

    out = f"UpdateList-{format_ts()}.txt"

    # --- 情况 1：一个参数 → 输出所有 URL ---
    if len(args) == 1:
        d = load_common_dict(args[0])
        if not d:
            print("未找到 common 段")
            sys.exit(0)

        with open(out, "w", encoding="utf-8") as f:
            for row in d.values():
                f.write(extract_url(row) + "\n")

        print("输出:", out)
        sys.exit(0)

    # --- 情况 2：两个参数 → 比较新增项 ---
    old = load_common_dict(args[0])
    new = load_common_dict(args[1])

    diff_keys = set(new.keys()) - set(old.keys())

    if not diff_keys:
        print("无新增条目")
        sys.exit(0)

    with open(out, "w", encoding="utf-8") as f:
        for k in diff_keys:
            f.write(extract_url(new[k]) + "\n")

    print("输出:", out)
