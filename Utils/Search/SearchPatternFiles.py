import re
from pathlib import Path
from typing import Pattern, List

# ====== 可配置区域 / Configurable Area ======
INPUT_PATH = r"D:\Tools\UsefulTools\MuMu\Shared\Download\DaoYou"

skel_pattern = re.compile(rb'\x07\d\.\d\.\d{1,2}')

key_words = ["SkeletonAnimation.create"]

def search(directory: str) -> List[Path]:
    """Recursively searches the directory and returns a list of all files."""
    if not directory:
        print("Please set the INPUT_PATH variable.")
        return []

    target_dir = Path(directory)
    if not target_dir.exists() or not target_dir.is_dir():
        print(f"Invalid directory: {directory}")
        return []

    # rglob("*") gets everything; we filter for is_file()
    return [p for p in target_dir.rglob("*") if p.is_file()]


def is_spine_json(file_path: Path) -> bool:
    if b'"skeleton":' in file_path.read_bytes():
        print(f"[SpineJson] {file_path}")
        return True
    return False


def is_spine_skel(file_path: Path) -> bool:
    if skel_pattern.search(file_path.read_bytes()):
        print(f"[SpineSkel] {file_path}")
        return True
    return False


def is_spine_atlas(file_path: Path) -> bool:
    if b'size:' in file_path.read_bytes():
        print(f"[SpineAtlas] {file_path}")
        return True
    return False

def is_live2d_moc(file_path: Path) -> bool:
    data = file_path.read_bytes()
    if b'MOC3' in data or b'moc' in data:
        print(f"[Live2DMoc] {file_path}")
        return True
    return False

def is_key_word_file(file_path: Path) -> bool:
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore").lower()
        for kw in key_words:
            if kw.lower() in content:
                print(f"[KeyWord] {file_path}", f"contains keyword: {kw}")
                return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    return False


def main():
    files = search(INPUT_PATH)

    if not files:
        return

    print(f"Scanning {len(files)} files...\n")
    print("-" * 40)

    for file_path in files:
        # We check them sequentially. If you only want a file to be categorized
        # as exactly one type, we can use `elif` to skip further checks.
        # if is_spine_json(file_path):
        #     continue
        # if is_spine_atlas(file_path):
        #     continue
        # if is_spine_skel(file_path):
        #     continue
        # if is_live2d_moc(file_path):
        #     continue
        if is_key_word_file(file_path):
            continue

    print("-" * 40)
    print("Scan complete.")


if __name__ == "__main__":
    main()