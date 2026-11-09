from pathlib import Path



def solve(source_dir: Path, output_dir: Path, conf_path: Path):
    try:
        pass
        print(f"[OK] {p}")
    except Exception as e:
        print(f"[FAIL] {p}: {e}")


if __name__ == "__main__":
    CONF_PATH = Path(r"")
    SOURCE_DIR = Path(r"")
    OUTPUT_DIR = Path(r"")
    
    for p in SOURCE_DIR.rglob("*"):
        try:
            solve(
                source_dir=p,
                output_dir=OUTPUT_DIR,
                conf_path=CONF_PATH
            )
            print(f"[OK] {p}")
        except Exception as e:
            print(f"[FAIL] {p}: {e}")