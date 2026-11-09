# 按 skel 引用自动收集多页并构建可加载的 Spine 组(.skel+.png+.atlas)
# - 页图: 自动解码(明文/签名/CCZ->PVR) + 分离 alpha 合并为 RGBA
# - 旋转修正: cocos 旋转帧内容在页内原地转 180 (Spine 3.5 约定相反)
# - atlas: 3.5 语法, region 原名 + 文件夹/名 前缀别名

import sys, io, shutil, plistlib
from pathlib import Path
sys.path.insert(0, r"D:\Games\GameUnpackAssets\mymodel\.Scripts")
sys.path.insert(0, r"D:\Games\GameUnpackAssets\mymodel\.Scripts\Games\illusionConnectRe")
from PIL import Image
import importlib.util
spec = importlib.util.spec_from_file_location("icr", r"D:\Games\GameUnpackAssets\mymodel\.Scripts\Games\illusionConnectRe\icr_decrypt.py")
icr = importlib.util.module_from_spec(spec); spec.loader.exec_module(icr)
from Utils.Png import Texture2Png as T
import cxxtea

ANIM = Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\illusionConnectRe\extract\asset\anim")
OUT_ROOT = Path(r"D:\Games\GameUnpackAssets\mymodel\.Scripts\Games\illusionConnectRe\_spine_test")
if OUT_ROOT.exists(): shutil.rmtree(OUT_ROOT)

def plain_bytes(p: Path) -> bytes:
    data = p.read_bytes()
    if not data.startswith(icr.SIGN_OTHER): return data
    ds = data[7:]
    key = icr.generate_key(ds[0], ds[1])
    dl = ds[5] | ((ds[4] | ((ds[3] | (ds[2] << 8)) << 8)) << 8)
    final = cxxtea.decrypt(ds[6:6 + dl], b"", key) + ds[6 + dl:]
    return icr.decompress_ccz(final) if final.startswith(b"CCZ!") else final

def to_image(plain: bytes):
    if plain[:4] == b"\x89PNG": return Image.open(io.BytesIO(plain))
    if plain[:4] in (b"PVR\x03", b"4\x00\x00\x00"): return T.decode_pvr(plain)
    raise ValueError("unknown " + plain[:4].hex())

def load_page_img(tex_name: str) -> Image.Image:
    # 优先同目录 tex_name.png，其次 .ccz / 全 extract 查找
    cands = [ANIM / (tex_name + ".png"), ANIM / (tex_name + ".ccz"), ANIM / tex_name]
    p = next((q for q in cands if q.exists()), None)
    if p is None:
        hits = list(Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\illusionConnectRe\extract").rglob(tex_name + ".png"))
        p = hits[0] if hits else None
    if p is None: raise FileNotFoundError(tex_name)
    img = to_image(plain_bytes(p))
    a_src = p.with_name(p.stem + ".png@alpha")
    if a_src.exists():
        try:
            a_img = to_image(plain_bytes(a_src)).convert("L")
            if a_img.size != img.size: a_img = a_img.resize(img.size)
            rgb = img.convert("RGB")
            img = Image.merge("RGBA", (*rgb.split(), a_img))
        except Exception as e:
            print("  alpha fail", tex_name, str(e)[:60])
    return img

# ---- 索引 anim plists: frame base -> pages(texFileName)
frame_page = {}
pages = {}
for pl in ANIM.rglob("*.plist"):
    try: d = plistlib.load(open(pl, "rb"))
    except Exception: continue
    meta = d.get("metadata", {}) or {}
    tex = meta.get("textureFileName") or (pl.stem + ".png")
    tex = tex.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    pages.setdefault(tex, {})
    for k in (d.get("frames", {}) or {}).keys():
        base = k.rsplit(".", 1)[0]
        if len(base) >= 5:
            pages[tex][base] = d["frames"][k]
            frame_page.setdefault(base, set()).add(tex)

# 要构建的组: skel 文件名(stem)，自动发现所需页面
GROUPS = ["portrait_abo", "portrait_dana_awaken"]
groups = GROUPS
for gname in groups:
    skel_src = ANIM / (gname + ".skel")
    if not skel_src.exists():
        print("no skel", gname); continue
    b = skel_src.read_bytes()
    gdir = OUT_ROOT / gname
    gdir.mkdir(parents=True)
    shutil.copy2(skel_src, gdir / (gname + ".skel"))
    # 该 skel 引用的 frame base（子串级，宁可多含）
    used = [fb for fb in frame_page if fb.encode() in b and len(fb) >= 4]
    need_pages = set()
    for fb in used: need_pages |= frame_page[fb]
    print(f"{gname}: used-frames={len(used)} pages={sorted(need_pages)}")
    # 多页 atlas + 页图
    blocks = []
    ok_pages = []
    for tex in sorted(need_pages):
        try:
            img = load_page_img(tex)
        except Exception as e:
            print("  page decode skip", tex, str(e)[:70]); continue
        img = img.convert("RGBA")
        import re as _re
        _RECT = _re.compile(r"\{\{(-?\d+),(-?\d+)},\{(-?\d+),(-?\d+)}}")
        _fixed = 0
        for base, fr in pages[tex].items():
            if not fr.get("textureRotated", fr.get("rotated", False)):
                continue
            m = _RECT.search(fr.get("textureRect") or fr.get("frame") or "")
            if not m:
                continue
            x, y, w, h = (int(g) for g in m.groups())
            box = (x, y, x + h, y + w)
            img.paste(img.crop(box).transpose(Image.Transpose.ROTATE_180), box)
            _fixed += 1
        if _fixed:
            print(f"  page {tex}: rotate180 x {_fixed}")
        img.save(gdir / (tex + ".png"), format="PNG")
        ok_pages.append(tex)
        # 只输出被该 skel 用到的帧（base + global/ 前缀别名）
        regs = []
        import re
        for base, fr in pages[tex].items():
            if base not in used: continue
            names = [base]
            for m in re.finditer(rb"([A-Za-z0-9_\-]+)/" + re.escape(base.encode()), b):
                pre = m.group(1).decode("latin1")
                nm2 = pre + "/" + base
                if nm2 not in names:
                    names.append(nm2)
            for nm in names:
                frr = pages[tex][base]
                regs.append((nm, frr))
        w, h = img.size
        blocks.append((tex, w, h, regs))
    lines = []
    for tex, w, h, regs in blocks:
        lines.append("")
        lines.append(tex + ".png")
        lines.append(f"size: {w}, {h}")
        lines.append("format: RGBA8888")
        lines.append("filter: Linear, Linear")
        lines.append("repeat: none")
        for nm, fr in regs:
            import re
            m = re.search(r"{{(-?\d+),(-?\d+)},\{(-?\d+),(-?\d+)}}", fr.get("textureRect") or fr.get("frame") or "")
            if not m: continue
            x, y, rw, rh = (int(g) for g in m.groups())
            rot = bool(fr.get("textureRotated", fr.get("rotated", False)))
            lines.append(nm)
            lines.append(f"  rotate: {'true' if rot else 'false'}")
            lines.append(f"  xy: {x}, {y}")
            lines.append(f"  size: {rw}, {rh}")
            lines.append(f"  orig: {rw}, {rh}")
            lines.append("  offset: 0, 0")
            lines.append("  index: -1")
    atl = gdir / (gname + ".atlas")
    atl.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  -> wrote {gname}.atlas pages={len(ok_pages)} regions={sum(len(r) for _,_,_,r in blocks)} files={sorted(x.name for x in gdir.iterdir())}")
print("done under", OUT_ROOT)
