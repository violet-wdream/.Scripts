import struct
from pathlib import Path
from multiprocessing import Pool, cpu_count

# 时尚百货城 纹理图decrypt


ENCRYPTED_MAGIC = b"wbqj"
key = b"wbqj2021"
def decrypt_png_data(encrypted: bytes) -> bytes:
    if not encrypted.startswith(ENCRYPTED_MAGIC):
        return encrypted
    header = struct.pack('<Q', 0xA1A0A0D474E5089)
    body = encrypted[7:]
    tail = (
            struct.pack("<I", 0) +
            b"IEND" +
            struct.pack(">I", 0xAE426082)
    )
    new_data = bytearray(header + body + tail)
    for i, b in enumerate(body):
        new_data[8 + i] = b ^ key[i % 8]
    return bytes(new_data)

def process_file(fpath: str):
    p = Path(fpath)
    raw = p.read_bytes()
    if not raw.startswith(b'\x89PNG\r\n\x1a\n'):
        p.write_bytes(decrypt_png_data(raw))

if __name__ == "__main__":
    root = Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\resources\native")
    files = [str(f) for f in root.rglob("*.png")]
    with Pool(cpu_count()) as pool:
        pool.map(process_file, files)