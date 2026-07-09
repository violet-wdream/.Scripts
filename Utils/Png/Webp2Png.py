from pathlib import Path
from PIL import Image

def webp_to_png(webp_path: Path, png_path: Path):
    with Image.open(webp_path) as img:
        img = img.convert("RGBA")  # 保证透明通道
        img.save(png_path, "PNG")

if __name__ == "__main__":
    root_dir = Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\HeiDong_crypto\avatar\hd_out")
    out_path = Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\HeiDong_crypto\out")
    for file in root_dir.rglob("*"):
        dat = file.read_bytes()
        if dat.startswith(b"RIFF") and dat[8:12] == b"WEBP":
            # file.rename(file.with_suffix(".webp"))
            filename = file.stem + ".png"
            # filename = file.stem.rsplit("-")[0] + ".png"

            out_file = out_path / filename
            webp_to_png(file, out_file)

