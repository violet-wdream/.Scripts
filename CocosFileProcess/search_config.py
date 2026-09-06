import json
from pathlib import Path

INPUT_PATH = r"D:\Tools\UsefulTools\MuMu\Shared\Download\Zgirls3\res"

def has_paths_and_uuids(obj):
    """
    递归判断 JSON 中是否同时存在 keys: 'paths' 和 'uuids'
    """
    if isinstance(obj, dict):
        keys = set(obj.keys())

        if "paths" in keys and "uuids" in keys:
            return True

        # 继续递归子节点
        return any(has_paths_and_uuids(v) for v in obj.values())

    elif isinstance(obj, list):
        return any(has_paths_and_uuids(i) for i in obj)

    return False


def search_json(root: Path):
    print(f"扫描目录: {root}\n")

    found = []

    for path in root.rglob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
        except OSError as e:
            continue

        if has_paths_and_uuids(data):
            found.append(path)

    if not found:
        print("没有找到符合条件的 JSON 文件")
        return

    print("符合条件的文件：\n")
    for f in found:
        print(f)


def main():
    root = Path(INPUT_PATH) if INPUT_PATH else Path.cwd()
    search_json(root)


if __name__ == "__main__":
    main()