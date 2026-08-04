from pathlib import Path
import hashlib

def md5_hash(s):
    return hashlib.md5(s.encode()).hexdigest()

def read_csv(csv: Path) -> dict[str, str]: # MD5 -> Path
    lines = csv.read_text(encoding="utf-8").splitlines()
    pd = {}
    for line in lines:
        if not line.strip() or 'path,' in line:  # Skip empty lines and header
            continue
        path, _, md5 = line.split(",")

        # if 'longnv.png' in path:
        #     print(f"longnv: {path}, {md5}")

        path_no_ext = path.rsplit(".", 1)[0]

        # md5 -> png path
        pd[md5] = path

        if not 'common_sken_res' in path: # Skip non-spine resources
            continue

        # md5 -> skel path
        skel_path = path_no_ext + ".skel"
        md5 = md5_hash(skel_path + ".bytes")
        pd[md5] = skel_path

        json_path = path_no_ext + ".json"
        md5 = md5_hash(json_path)
        pd[md5] = json_path

        # md5 -> atlas path
        atlas_path = path_no_ext + ".atlas"
        md5 = md5_hash(atlas_path + ".txt")
        pd[md5] = atlas_path

        md5 = md5_hash(atlas_path)
        pd[md5] = atlas_path

    return pd


if __name__ == "__main__":
    csv_path = Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\DaoYou\pathlist.csv")
    md5_file_path = Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\DaoYou\out")
    out_path = Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\DaoYou\out-out")

    path_dict = read_csv(csv_path)
    is_md5_found = {md5: False for md5 in path_dict.keys()}

    print(f"Loaded {len(path_dict)} entries from CSV")

    for file in md5_file_path.rglob("*"):
        if not file.is_file():
            continue

        md5_name = file.name.rsplit(".", 1)[0]  # Remove extension
        if len(md5_name) != 32:
            continue
        if md5_name in path_dict:
            # print(f"{file.name} -> {path_dict[md5_name]}")
            is_md5_found[md5_name] = True
            # move as out_path / path_dict[md5_name]
            target_path = out_path / path_dict[md5_name]
            target_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                if target_path.exists():
                    continue
                file.rename(target_path)
            except Exception as e:
                print(f"Error moving {file} to {target_path}: {e}")
        else:
            # print(f"{file.name} -> Not found")
            pass

    not_found = 0
    for md5, found in is_md5_found.items():
        if not found:
            not_found += 1
            # print(f"{md5} -> {path_dict[md5]}")
    print(f"Not Used: {not_found} / {len(path_dict)}")
    # print(path_dict)