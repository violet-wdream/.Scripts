from pathlib import Path

def solve(source_dir: Path, output_dir: Path, conf_dir: Path):
    try:
        pass
        print(f"[OK] {p}")
    except Exception as e:
        print(f"[FAIL] {p}: {e}")


if __name__ == "__main__":
    input_path = Path(r"")
    output_path = Path(r"")
    # conf_path = Path(r"") # optional
    
    for p in input_path.rglob("*"):
        try:
            solve(
                source_dir=p,
                output_dir=output_path
                # conf_dir=conf_path
            )
            print(f"[OK] {p}")
        except Exception as e:
            print(f"[FAIL] {p}: {e}")