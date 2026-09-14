# References: https://github.com/AXiX-official/UnityAnimeGamesInfo/blob/main/Info/OnePercent/DBreeze.py

import os
import lz4.frame
import re
from pathlib import Path
from PIL.Image import Image
from UnityPy.classes import Texture2D, GLTextureSettings
from UnityPy.export import Texture2DConverter

DBreezeResources_PATH = r"D:\Tools\UsefulTools\MuMu\Shared\Download\Database\_DBreezeResources"
OUTPUT_PATH = r"D:\Tools\UsefulTools\MuMu\Shared\Download\100\Output"

PATTERN_RE = re.compile(
    b'(utxt\\.|ubin\\.|utex2\\.)'
)

# 百分之一(Hundredth/ onePercent) 这个游戏使用了旧版的live2d, 所以使用了moc 以及 mtn 动作
# 所有文件类型都是 'u' 开头 utype, 主要提取三个类型 utxt, ubin, utex2
# 这里不打算整体解析整个文件, 只提取出其中的单元数据, 其他的头部信息和索引表等不做处理
# 提取单元结构为:
# name_length 1B BE
# data_length 4B BE
# name name_length B LE
# data data_length B LE
# 先搜索文件类型的字节, 再向前得到 name_length 和 file_length, 最后提取 name 和 data

#1. utxt - model/exp
# 75 74 78 74 utxt.l2d.path.name.model / utxt.l2d.path.name.exp -> 导出为 ./l2d/path/name.model.json 或者 name.exp.json
# 名称结束后紧跟着 '{' 开始的 json 明文, 需要去掉中间填充的非法字符, 以'}' 结束

#2. ubin - mtn
# 75 62 69 6E ubin.l2d.path.name.mtn -> 导出为 ./l2d/path/name.mtn
# 名称结束后紧跟着数据也就是 mtn 固定头部`# Live2D Animator Motion Data`
# 一直读到 0D 00 作为终止符结束(mtn 包括0D但是不包括这个00), 但是如果数据长度没问题, 就直接按照长度读取, 可以用这个终止符作为检测标准
# 2. ubin - moc
# 75 62 69 6E ubin.l2d.path.name.moc ->  导出为 ./l2d/path/name.moc
# 名称结束后有 21B 的压缩数据(LZ4 Frame Header) 需要通过 LZ4解压, 解压后的数据以 moc 开头, 以 88 88 88 88 作为终止符结束(包括这个终止符)

#3. utex2.l2d.path.texture_00 -> 导出为 ./l2d/path/texture_00.png
# 名称读到字节 04 / 02 结束(名称不包括 04 / 02)
# 如果是名称结束后是第一个字节是 04 那么后疑似有包括04在内的 21B 的多余数据,因为后面的数据很像 ubin - moc 中多的 21B 数据
# 其实是 04 22 4D 18 这四个字节(LZ4 Frame Header)加上另外的17B的数据, 这里表示图像需要通过 LZ4解压data部分,再通过unity的图像格式提取
# 如果是 02 则说明直接无缝衔接了(包括 02 在内) Unity Serialized Object 直接通过unity的图像格式提取, 这里的图像数据不需要解压
# data data_length B
#     LZ4 Frame Header 21B
#     Unity Serialized Object ?B
#     raw image data ?B
# 暂时只提取出LZ4解压数据, 保留为Unity序列化数据
#3. utex2.tt_* -> 导出为 ./Textures2D/tt_*.png


def read_property(prop_name: str, data: bytes) -> int:
    # 编码为 UTF-16 小端
    marker = prop_name.encode('utf-16-le')
    idx = data.find(marker)
    if idx == -1:
        return 0
    val_start = idx + len(marker)
    return read_int_le(data, val_start, 4)

def read_int_be(data: bytes, offset: int, length: int) -> int:
    return int.from_bytes(data[offset: offset + length], byteorder='big')
def read_int_le(data: bytes, offset: int, length: int) -> int:
    return int.from_bytes(data[offset: offset + length], byteorder='little')

def extract_unity_texture(data: bytes, save_path: str) :
    width = read_property("Width", data) # 0x11D
    height = read_property("Height", data) # 0x133
    fmt_int = read_property("Format", data) # 0x160

    content_marker = "System.Byte[], mscorlib".encode('utf-16-le')
    content_idx = data.find(content_marker)
    payload_start = content_idx + len(content_marker) + 1 + 12 # 0x1C1

    image_data = data[payload_start:]
    tpl_settings = GLTextureSettings(
        m_FilterMode=1,
        m_Aniso=1,
        m_MipBias=0,
        m_WrapMode=0
    )
    tex_dic = {
        "image_data": image_data,
        "m_CompleteImageSize": len(image_data),
        "m_Height": height,
        "m_ImageCount": 1,
        "m_IsReadable": True,
        "m_LightmapFormat": 0,
        "m_Name": "",
        "m_TextureDimension": 2, # 2D
        "m_TextureFormat": fmt_int,
        "m_TextureSettings": tpl_settings,
        "m_Width": width,
    }

    tex2d: Texture2D = Texture2D(**tex_dic)

    image: Image = Texture2DConverter.get_image_from_texture2d(tex2d)
    if image:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        image.save(save_path)
    else:
        print("[-] 纹理数据解析失败")

def extract_utxt_model_exp(data: bytes) -> bytes:
    # 名称结束后紧跟着 '{' 开始的 json 明文, 需要去掉中间填充的非法字符, 以'}' 结束
    start_idx = data.find(b'{')
    end_idx = data.rfind(b'}')

    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        return data[start_idx: end_idx + 1]
    return b""

def extract_ubin_mtn(data: bytes) -> bytes:
    # 读到 0D 00 作为终止符结束 (包括 0D，不包括 00)
    # 如果找到了 # Live2D Animator Motion Data 头部，再进行截断
    if b"# Live2D Animator Motion Data" in data:
        end_idx = data.find(b'\x0D\x00')
        if end_idx != -1:
            return data[: end_idx + 1]  # 切片到 0D 结束
        return data  # 如果没找到 0D 00，直接返回根据 length 截取的数据
    return b""

def extract_ubin_moc(data: bytes) -> bytes:
    if data[:4] == b'\x04\x22\x4D\x18':
        try:
            print("[+] 检测到 LZ4 压缩 moc，正在解压...")
            decompressed_data = lz4.frame.decompress(data)
            return decompressed_data
        except Exception as e:
            print(f"[-] LZ4 解压失败: {e}")
            return b""
    else:
        return b""

def extract_utex2(data: bytes, name_str: str) -> None:
    if not data:
        return
    parts = name_str.split('.')
    if name_str.startswith("utex2.l2d"):
        # utex2.l2d.path.texture_00 -> ./l2d/path/texture_00.png
        # dirs = parts[1:-1] + ["textures"] # 这里的配置文件里没有 textures 这个文件夹, 直接放在 path 下了
        dirs = parts[1:-1]
        filename = f"{parts[-1]}.png"
        save_path = os.path.join(OUTPUT_PATH, *dirs, filename)
    else:
        dirs = ["Textures2D"]
        filename = f"{parts[-1]}.png"
        save_path = os.path.join(OUTPUT_PATH, *dirs, filename)

    # 第一字节判断格式
    if data[:4] == b'\x04\x22\x4D\x18':
        try:
            print("[+] 检测到 LZ4 压缩 tex，正在解压...")
            decompressed_data = lz4.frame.decompress(data)
            extract_unity_texture(decompressed_data, save_path)
            return

        except Exception as e:
            print(f"[-] LZ4 解压失败: {e}")
            return

    elif data[0] == 0x02:
        extract_unity_texture(data, save_path)
        return


def save_file(output_dir: str, name_str: str, clean_data: bytes):
    if not clean_data:
        return
    parts = name_str.split('.')
    if name_str.startswith("utxt."):
        # utxt.l2d.path.name.model/exp -> ./l2d/path/name.model/exp.json
        dirs = parts[1:-2]
        if name_str.endswith(".exp"):
            dirs.append("expressions")
        filename = f"{parts[-2]}.{parts[-1]}.json"

    elif name_str.startswith("ubin."):
        # ubin.l2d.path.name.mtn/moc -> ./l2d/path/motions/name.mtn
        dirs = parts[1:-2]
        if name_str.endswith(".mtn"):
            dirs.append("motions")
        filename = f"{parts[-2]}.{parts[-1]}"

    else:
        return

    out_path = os.path.join(output_dir, *dirs)
    os.makedirs(out_path, exist_ok=True)
    file_path = os.path.join(out_path, filename)

    with open(file_path, "wb") as f:
        f.write(clean_data)
    print(f"[+] 提取成功: {file_path}")

def main():
    if not os.path.exists(DBreezeResources_PATH):
        print("未找到_DBreezeResources，请检查路径")
        return

    with open(DBreezeResources_PATH, "rb") as f:
        data = f.read()

    file_length = len(data)

    for m in PATTERN_RE.finditer(data):
        i = m.start()
        name_len_idx = i - 5
        data_len_idx = i - 4
        if name_len_idx < 0:
            continue
        name_length = data[name_len_idx]
        data_length = read_int_be(data, data_len_idx, 4)
        name_bytes = data[i: i + name_length]
        end_pos = len(name_bytes)
        for j, b in enumerate(name_bytes):
            if b in (0x00, 0x02, 0x04):
                end_pos = j
                break
        try:
            name_str = name_bytes[:end_pos].decode('ascii', errors='ignore')
        except UnicodeDecodeError:
            continue

        data_start = i + name_length
        data_end = data_start + data_length
        if data_end > file_length:
            print(f"[-] 越界: {name_str}")
            continue
        data_chunk = data[data_start: data_end]

        if name_str.startswith("utxt.l2d") and (name_str.endswith(".model") or name_str.endswith(".exp")):
            clean_data = extract_utxt_model_exp(data_chunk)

        elif name_str.startswith("ubin.l2d"):
            if name_str.endswith(".mtn"):
                clean_data = extract_ubin_mtn(data_chunk)
            elif name_str.endswith(".moc"):
                clean_data = extract_ubin_moc(data_chunk)
            else:
                clean_data = data_chunk

        elif name_str.startswith("utex2"):
            extract_utex2(data_chunk, name_str) #单独保存
            continue
        else:
            continue

        save_file(OUTPUT_PATH, name_str, clean_data)

    print("解析完毕")



if __name__ == "__main__":
    main()
