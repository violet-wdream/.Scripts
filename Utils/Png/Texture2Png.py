import bz2
import gzip
import math
import struct
import zlib
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageChops
import texture2ddecoder as t2d

ASTC_MAGIC = b"\x13\xAB\xA1\x5C"
PKM_MAGIC = b"PKM "
PVR3_MAGIC = b"PVR\x03"
PVR2_MAGIC = b"4\x00\x00\x00"
CCZ_SIGS = (b"CCZ!", b"CCZp")
PVR2_TAG = b"PVR!"

PKM_DECODERS = {
    0: ("ETC1", t2d.decode_etc1),
    1: ("ETC2", t2d.decode_etc2),
    2: ("ETC2 RGBA8", t2d.decode_etc2a8),
    3: ("ETC2 RGB8A1", t2d.decode_etc2a1),
    4: ("ETC2 RGBA8", t2d.decode_etc2a8),
    5: ("EAC R11", t2d.decode_eacr),
    6: ("EAC RG11", t2d.decode_eacrg),
    7: ("EAC R11 signed", t2d.decode_eacr_signed),
    8: ("EAC RG11 signed", t2d.decode_eacrg_signed),
}

CODEC_SUFFIXES = (".pvr.ccz", ".pkm", ".astc", ".bptc", ".webp", ".pvr", ".ccz")


def _out_stem(p: Path) -> str:
    name = p.name
    for ext in CODEC_SUFFIXES:
        if name.lower().endswith(ext):
            return name[: -len(ext)]
    return p.stem


def _img_rgba_bgra(data: bytes, w: int, h: int) -> Image.Image:
    return Image.frombytes("RGBA", (w, h), data, "raw", ("BGRA",))


def _img_from_bgra(data: bytes, w: int, h: int, premultiplied: bool = False) -> Image.Image:
    if premultiplied:
        return Image.frombytes("RGBA", (w, h), _bgra_to_rgba(data, True))
    return _img_rgba_bgra(data, w, h)


def _pkm_dims(data: bytes):
    return int.from_bytes(data[12:14], "big"), int.from_bytes(data[14:16], "big")


def decode_pkm(data: bytes) -> tuple:
    if data[:4] != PKM_MAGIC:
        raise ValueError("不是有效的 PKM 文件")
    if data[4:6] not in (b"10", b"20"):
        raise ValueError("不支持的 PKM 版本")
    fmt = int.from_bytes(data[6:8], "big")
    if fmt not in PKM_DECODERS:
        raise ValueError(f"不支持的 PKM format: {fmt}")
    name, decoder = PKM_DECODERS[fmt]
    w, h = _pkm_dims(data)
    return name, _img_rgba_bgra(decoder(data[16:], w, h), w, h)


def decode_astc(data: bytes) -> Image.Image:
    if data[:4] != ASTC_MAGIC:
        raise ValueError("非标准 ASTC 文件")
    bw, bh = data[4], data[5]
    w = data[7] | (data[8] << 8) | (data[9] << 16)
    h = data[10] | (data[11] << 8) | (data[12] << 16)
    return _img_rgba_bgra(t2d.decode_astc(data[16:], w, h, bw, bh), w, h)


def decode_bptc(data: bytes) -> Image.Image:
    side = math.isqrt(len(data))
    if side * side != len(data):
        raise ValueError(f"{len(data)} 非完全平方数，无法推断宽高")
    return _img_rgba_bgra(t2d.decode_bc7(data, side, side), side, side)


def decompress_ccz(data: bytes) -> bytes:
    sig, comp_type, _ver, _reserved, _length = struct.unpack(">4sHHII", data[:16])
    if sig not in CCZ_SIGS:
        raise ValueError(f"无法识别的CCZ签名: {sig}")
    payload = data[16:]
    if comp_type == 0:
        return zlib.decompress(payload)
    if comp_type == 1:
        return bz2.decompress(payload)
    if comp_type == 2:
        return gzip.decompress(payload)
    if comp_type == 3:
        return payload
    return zlib.decompress(payload)


def _bgra_to_rgba(data: bytes, premultiplied: bool) -> bytes:
    buf = bytearray(data)
    for i in range(0, len(buf), 4):
        b, g, r, a = buf[i], buf[i + 1], buf[i + 2], buf[i + 3]
        if premultiplied:
            if a == 0:
                r = g = b = 0
            else:
                r = min(255, round(r * 255 / a))
                g = min(255, round(g * 255 / a))
                b = min(255, round(b * 255 / a))
        buf[i], buf[i + 1], buf[i + 2] = r, g, b
    return bytes(buf)


_PVR3_BLOCK_DECODERS = {
    6: ("ETC1", t2d.decode_etc1, 8),
    22: ("ETC2 RGB", t2d.decode_etc2, 8),
    23: ("ETC2 RGBA", t2d.decode_etc2a8, 16),
    24: ("ETC2 RGB A1", t2d.decode_etc2a1, 8),
    25: ("EAC R11", t2d.decode_eacr, 8),
    26: ("EAC RG11", t2d.decode_eacrg, 16),
}


def _pvr3_decode_block(data: bytes, width: int, height: int, decoder, block_bytes: int) -> bytes:
    need = ((width + 3) // 4) * ((height + 3) // 4) * block_bytes
    if len(data) < need:
        data = data + b"\x00" * (need - len(data))
    return decoder(data, width, height)


def _pvr3_guess_decode(pixel_data: bytes, width: int, height: int, pixel_format: int) -> bytes:
    full = width * height
    if len(pixel_data) == full:
        return _pvr3_decode_block(pixel_data, width, height, t2d.decode_etc2a8, 16)
    if len(pixel_data) == full // 2:
        return _pvr3_decode_block(pixel_data, width, height, t2d.decode_etc1, 8)
    raise ValueError(f"未知 PVR3 像素格式: {hex(pixel_format)} (payload {len(pixel_data)}B)")


_565_TAB_R = [(h >> 3) << 3 for h in range(256)]
_565_TAB_B = [(l & 0x1F) << 3 for l in range(256)]
_565_TAB_GLO = [l >> 5 for l in range(256)]
_565_TAB_GSHI = [(h & 0x07) << 3 for h in range(256)]
_565_TAB_G6 = [g << 2 for g in range(256)]


def _img_rgb565(data: bytes, width: int, height: int, little_endian: bool = True) -> Image.Image:
    n = width * height
    need = n * 2
    if len(data) < need:
        raise ValueError(f"RGB565 数据不足: {len(data)}B < {need}B")
    # 小端: 首字节为低8位; 大端(如 PVRv2 0x13): 首字节为高8位
    if little_endian:
        lo_src, hi_src = data[:need:2], data[1:need:2]
    else:
        lo_src, hi_src = data[1:need:2], data[:need:2]
    lo = Image.frombytes("L", (width, height), lo_src)
    hi = Image.frombytes("L", (width, height), hi_src)
    r = hi.point(_565_TAB_R)
    b = lo.point(_565_TAB_B)
    g = lo.point(_565_TAB_GLO)
    g = ImageChops.add(g, hi.point(_565_TAB_GSHI))
    g = g.point(_565_TAB_G6)
    return Image.merge(
        "RGBA", (r, g, b, Image.new("L", (width, height), 255))
    )


def _img_a8(data: bytes, width: int, height: int) -> Image.Image:
    if len(data) >= width * height:
        lum = Image.frombytes("L", (width, height), data[: width * height])
        return Image.merge("RGBA", (lum, lum, lum, lum))
    raw = bytearray(len(data) * 4)
    for i, v in enumerate(data):
        j = i * 4
        raw[j] = raw[j + 1] = raw[j + 2] = raw[j + 3] = v
    return Image.frombytes("RGBA", (width, height), bytes(raw))


def _unpremul_rgba(data: bytes) -> bytes:
    buf = bytearray(data)
    for i in range(0, len(buf), 4):
        a = buf[i + 3]
        if a == 0:
            buf[i] = buf[i + 1] = buf[i + 2] = 0
        elif a != 255:
            buf[i] = min(255, round(buf[i] * 255 / a))
            buf[i + 1] = min(255, round(buf[i + 1] * 255 / a))
            buf[i + 2] = min(255, round(buf[i + 2] * 255 / a))
    return bytes(buf)


def _img_rgba8888(data: bytes, width: int, height: int, premultiplied: bool = False) -> Image.Image:
    need = width * height * 4
    if len(data) < need:
        raise ValueError(f"RGBA8888 数据不足: {len(data)}B < {need}B")
    raw = data[:need]
    if premultiplied:
        raw = _unpremul_rgba(raw)
    return Image.frombytes("RGBA", (width, height), raw)


def _pvr3_raw_decode(
    data: bytes,
    width: int,
    height: int,
    pf_bytes: bytes,
    premultiplied: bool = False,
) -> Image.Image:
    order = pf_bytes[:4]
    bits = pf_bytes[4:8]
    if order[:4] == b"rgba" and bits[:4] == b"\x08\x08\x08\x08":
        return _img_rgba8888(data, width, height, premultiplied)
    if order[:3] == b"rgb" and bits[:3] == b"\x05\x06\x05":
        return _img_rgb565(data, width, height)
    if order[0:1] == b"a" and bits[0] == 8:
        return _img_a8(data, width, height)
    raise ValueError(f"未知 PVR3 未压缩通道格式: {order!r} + {bits!r}")


def decode_pvr(data: bytes) -> Image.Image:
    if data[:4] == PVR3_MAGIC:
        (
            flags,
            pixel_format,
            colour_space,
            channel_type,
            height,
            width,
            depth,
            num_surfaces,
            num_faces,
            mipmaps,
            metadata_size,
        ) = struct.unpack("<IQIIIIIIIII", data[4:52])
        
        pixel_data = data[52 + metadata_size:]
        
        entry = _PVR3_BLOCK_DECODERS.get(pixel_format) if pixel_format < (1 << 32) else None
        if entry is not None:
            rgba = _pvr3_decode_block(pixel_data, width, height, entry[1], entry[2])
            return _img_from_bgra(rgba, width, height, premultiplied=bool(flags & 0x02))
        if pixel_format >= (1 << 32):
            pf_bytes = pixel_format.to_bytes(8, "little")
            return _pvr3_raw_decode(
                pixel_data, width, height, pf_bytes, premultiplied=bool(flags & 0x02)
            )
        rgba = _pvr3_guess_decode(pixel_data, width, height, pixel_format)
        return _img_from_bgra(rgba, width, height, premultiplied=bool(flags & 0x02))
    
    if data[:4] == PVR2_MAGIC:
        if data[44:48] != PVR2_TAG:
            raise ValueError("疑似 PVRv2，但未找到 'PVR!' 签名")
        header_length, height, width, _mips, flags, data_length = struct.unpack("<13I", data[0:52])[:6]
        pixel_format_code = flags & 0xFF
        if pixel_format_code == 0x36:
            raise ValueError("ETC1 压缩格式，需要更换专门的 ETC1 解码器")
        if pixel_format_code in (0x18, 0x19, 0x1A, 0x1B):
            pvr_data = data[52: 52 + data_length]
            n = width * height
            if len(pvr_data) == n:
                return _img_a8(pvr_data, width, height)  # 实际为 8bit alpha 页
            is_2bpp = pixel_format_code in (0x18, 0x1A)
            need = n // (4 if is_2bpp else 2)
            if len(pvr_data) >= need:
                raw = t2d.decode_pvrtc(pvr_data[:need], width, height, is_2bpp)
                return _img_rgba_bgra(raw, width, height)
            raise ValueError(f"PVRTC 数据不足: {len(pvr_data)}B")
        if pixel_format_code == 0x10:
            raise ValueError("RGBA4444 (16位) 格式，需要做像素位转换")
        if pixel_format_code == 0x13:
            return _img_rgb565(data[52: 52 + data_length], width, height, little_endian=True)
        if pixel_format_code != 0x12:
            raise ValueError(f"未知的 PVRv2 像素格式代码: {hex(pixel_format_code)}")
        pixel_data = data[52: 52 + data_length]
        return Image.frombytes("RGBA", (width, height), pixel_data)
    raise ValueError("无法识别的 PVR/CCZ 文件")


def _is_raw_bc7(data: bytes) -> bool:
    if data[:4] in (PKM_MAGIC, ASTC_MAGIC, PVR3_MAGIC, PVR2_MAGIC) or data[:4] in CCZ_SIGS:
        return False
    if data[:4] == b"\x89PNG" or data[:3] == b"\xff\xd8\xff" or data[:2] in (b"BM", b"GIF") or data[:4] == b"RIFF":
        return False
    if len(data) < 1024:
        return False
    side = math.isqrt(len(data))
    return side * side == len(data)

def texture2png(source_file: Path, output_dir: Path, delete_source: bool = False):
    p = source_file
    if not p.is_file():
        return False

    out = output_dir / f"{_out_stem(p)}.png"
    out.parent.mkdir(parents=True, exist_ok=True)

    data = p.read_bytes()
    header = data[:4]
    if header == PKM_MAGIC:
        name, img = decode_pkm(data)
        img.save(out)
        if delete_source:
            p.unlink(missing_ok=True)
        return True
    if header == ASTC_MAGIC:
        decode_astc(data).save(out)
        if delete_source:
            p.unlink(missing_ok=True)
        return True
    if header in CCZ_SIGS:
        data = decompress_ccz(data)
        decode_pvr(data).save(out)
        if delete_source:
            p.unlink(missing_ok=True)
        return True
    if header in (PVR3_MAGIC, PVR2_MAGIC):
        decode_pvr(data).save(out)
        if delete_source:
            p.unlink(missing_ok=True)
        return True
    if header == b"RIFF" and data[8:12] == b"WEBP":
        with Image.open(BytesIO(data)) as img:
            img.convert("RGBA").save(out)
        if delete_source:
            p.unlink(missing_ok=True)
        return True
    if p.suffix.lower() in (".bptc", ".bc7") or _is_raw_bc7(data):
        decode_bptc(data).save(out)
        if delete_source:
            p.unlink(missing_ok=True)
        return True
    return False



if __name__ == "__main__":
    SOURCE_DIR = Path(r"data")
    OUTPUT_DIR = Path(r"result")

    for texture in SOURCE_DIR.rglob("*"):
        try:
            ok = texture2png(source_file=texture,
                             output_dir=OUTPUT_DIR,
                             delete_source=False)
            if ok:
                print(f"[OK] {texture}")
        except Exception as e:
            print(f"[FAIL] {texture}: {e}")