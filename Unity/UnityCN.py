import os
import UnityPy

key_hex = "64313131383539633334346134363765"
input_dir = r"C:\Users\86182\Downloads\TEMP\test"
output_dir = r"C:\Users\86182\Downloads\TEMP\output"

key_bytes = bytes.fromhex(key_hex)
UnityPy.set_assetbundle_decrypt_key(key_bytes)

def strip_fake_header(_data: bytes) -> bytes:
    magic = b"UnityFS"
    index = _data[:0x2000].find(magic)
    if index > 0:
        print(f"[AutoStrip] Offset 0x{index:X}")
        return _data[index:]
    return _data


for root, _, files in os.walk(input_dir):
    for name in files:
        in_path = os.path.join(root, name)
        out_path = os.path.join(output_dir, os.path.relpath(in_path, input_dir))

        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        try:
            env = UnityPy.load(in_path)
            data = env.file.save()
            data = strip_fake_header(data) # auto strip fake header if exists

            with open(out_path, "wb") as f:
                f.write(data)

        except Exception as e:
            print("Failed:", in_path, e)