# coding=utf-8
import subprocess
from pathlib import Path
# https://github.com/zhukunqian/pkm2png

INPUT_PATH = Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\Zgirls3\Textures")


ETCPACK_DIR = Path(r"D:\Tools\ReverseTools\Pkm2png\pkm2png-master")
ETCPACK_EXE = ETCPACK_DIR / "etcpack.exe"
# =================
def convert_pkm_to_png(pkm_path: Path):
    out_dir = pkm_path.parent

    print(f"convert: {pkm_path}")

    # 执行转换
    result = subprocess.run(
        [
            str(ETCPACK_EXE),
            str(pkm_path),
            str(out_dir),
            "-ext", "PNG"
        ],
        cwd=ETCPACK_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # ===== 判断是否成功 =====
    # etcpack 输出文件名规则：原名 + .png
    out_png = out_dir / (pkm_path.stem + ".png")

    if result.returncode == 0 and out_png.exists():
        print(f"[OK] {out_png}")

        try:
            pkm_path.unlink()  # 删除原 pkm
        except Exception as e:
            print(f"[WARN] delete failed: {pkm_path} -> {e}")
    else:
        print(f"[FAIL] {pkm_path}")


def main():
    pkm_files = list(INPUT_PATH.rglob("*.pkm"))

    for pkm in pkm_files:
        convert_pkm_to_png(pkm)

    print("Done.")


if __name__ == "__main__":
    main()