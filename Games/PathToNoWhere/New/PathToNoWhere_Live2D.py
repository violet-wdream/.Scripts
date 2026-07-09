# 2026.5.14 无期迷途 (Path To No Where) 更新后 文件系统发生了一些变化
# fade 之前的 "ParameterIdHashes" 被改为 "ControlIds", 正好解决了之前 hash 无法还原为参数名的问题
# 目前猜测这里的 ControlIds 可能是索引, 然后通过参数列表还原为参数名
# 不过之前恰好做过解析 moc3 得到参数列表的工作

# References:
# https://github.com/aelurum/AssetStudio/blob/AssetStudioMod/AssetStudioUtility/CubismLive2DExtractor/Live2DExtractor.cs
# https://github.com/aelurum/AssetStudio/blob/AssetStudioMod/AssetStudioUtility/CubismLive2DExtractor/CubismMotion3Json.cs#L101
import ctypes
import math
from pathlib import Path
import os
import json
import re
# 这里需要使用 Live2DCubismCore.dll 来解析 moc3 文件
# https://www.live2d.com/zh-CHS/sdk/download/native/
os.add_dll_directory(
    r"D:\Games\GameUnpackAssets\mymodel\.Scripts\Live2DFileConvert\src"
)# Live2DCubismCore.dll 的路径 根据实际情况修改
core = ctypes.cdll.LoadLibrary("Live2DCubismCore.dll")

# 工作目录
ROOT_DIR = r"C:\Users\86182\Downloads\test"
# 可根据实际情况修改
FADE_PATH = ROOT_DIR + r"\Fade"
MOC3_JSON_PATH = ROOT_DIR + r"\Moc3Json"
TEXTURES_PATH = ROOT_DIR + r"\Textures"
TEXTURES_META_PATH = ROOT_DIR + r"\TexturesMeta"
OUTPUT_PATH = ROOT_DIR + r"\Output"



def json2moc3(path: str, output: str):
    """
        递归搜索 path 下所有 json 文件，
        如果存在 "_bytes" 字段，则导出为 .moc3 文件。

        输出结构：
        output/
            模型名/
                模型名.moc3
    """
    input_dir = Path(path)
    output_dir = Path(output)
    if not input_dir.exists():
        raise FileNotFoundError(f"输入目录不存在: {input_dir}")
    count = 0
    for json_file in input_dir.rglob("*.json"):
        try:
            # 尝试读取 json
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not data:
                raise ValueError("JSON 为空")

            bytes_data = data.get("_bytes")
            if not isinstance(bytes_data, list):
                continue

            # 获取模型名
            model_name = (data.get("m_Name") or json_file.stem).split(".")[0]
            model_dir = output_dir / model_name
            model_dir.mkdir(parents=True, exist_ok=True)

            # 输出文件
            moc3_path = model_dir / f"{model_name}.moc3"
            # 写入
            with open(moc3_path, "wb") as f:
                f.write(bytes(bytes_data))

            print(f"[OK] {json_file} -> {moc3_path}")
            count += 1

        except Exception as e:
            print(f"[FAIL] {json_file}: {e}")
    print(f"\n导出 {count} 个 moc3")

# https://docs.live2d.com/wp-content/uploads/2018/06/NativeCoreAPIReference_r2.pdf
def init_live2d_core():
    # initialize function signatures
    c_void_p = ctypes.c_void_p
    c_int = ctypes.c_int
    c_char_p = ctypes.c_char_p

    core.csmReviveMocInPlace.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32]
    core.csmReviveMocInPlace.restype = c_void_p

    core.csmGetSizeofModel.argtypes = [c_void_p]
    core.csmGetSizeofModel.restype = ctypes.c_uint32

    core.csmInitializeModelInPlace.argtypes = [c_void_p, c_void_p, ctypes.c_uint32]
    core.csmInitializeModelInPlace.restype = c_void_p

    core.csmGetParameterCount.argtypes = [c_void_p]
    core.csmGetParameterCount.restype = c_int
    core.csmGetParameterIds.argtypes = [c_void_p]
    core.csmGetParameterIds.restype = ctypes.POINTER(c_char_p)

    core.csmGetPartCount.argtypes = [c_void_p]
    core.csmGetPartCount.restype = c_int
    core.csmGetPartIds.argtypes = [c_void_p]
    core.csmGetPartIds.restype = ctypes.POINTER(c_char_p)

def extract_params_parts(moc3_path) -> tuple[list[str], list[str]]:
    # 粗略的解析方案, 需要手动对齐内存地址
    if not Path(moc3_path).exists():
        raise FileNotFoundError(f"文件不存在: {moc3_path}")

    data = Path(moc3_path).read_bytes()
    size = len(data)
    # 多分配 64 字节以确保有足够的空间进行地址平移
    moc_raw_buf = ctypes.create_string_buffer(size + 64)
    moc_raw_addr = ctypes.addressof(moc_raw_buf)

    # 位运算：计算出下一个满足 64 字节对齐的绝对地址
    moc_aligned_addr = (moc_raw_addr + 63) & ~63

    # 将文件数据精准复制到对齐后的安全内存区域中
    ctypes.memmove(moc_aligned_addr, data, size)
    moc_ptr = ctypes.cast(moc_aligned_addr, ctypes.POINTER(ctypes.c_ubyte))

    moc = core.csmReviveMocInPlace(
        moc_ptr,
        ctypes.c_uint32(size)
    )

    if not moc:
        raise RuntimeError(f"=== Invalid moc3 (内存未对齐或文件损坏)")

    model_size = core.csmGetSizeofModel(moc)
    # 多分配 16 字节用于平移对齐
    model_raw_buf = ctypes.create_string_buffer(model_size + 16)
    model_raw_addr = ctypes.addressof(model_raw_buf)

    # 位运算
    model_aligned_addr = (model_raw_addr + 15) & ~15
    model_ptr = ctypes.c_void_p(model_aligned_addr)

    model = core.csmInitializeModelInPlace(moc, model_ptr, model_size)
    if not model:
        raise RuntimeError("Model init failed")

    param_count = core.csmGetParameterCount(model)
    param_ids_ptr = core.csmGetParameterIds(model)

    part_count = core.csmGetPartCount(model)
    part_ids_ptr = core.csmGetPartIds(model)

    param_ids = []
    for i in range(param_count):
        param_ids.append(ctypes.string_at(param_ids_ptr[i]).decode("utf-8"))

    part_ids = []
    for i in range(part_count):
        part_ids.append(ctypes.string_at(part_ids_ptr[i]).decode("utf-8"))

    return param_ids, part_ids

def convert_segments(curve, force_bezier=True):
    """
    Unity Keyframe -> Live2D motion3 Segments
    """
    if not curve:
        return []

    segments = []

    # 第一个点直接写入
    first = curve[0]
    segments.append(first.get("time", 0.0))
    segments.append(first.get("value", 0.0))

    j = 1

    while j < len(curve):
        cur = curve[j]
        prev = curve[j - 1]
        next_curve = curve[j + 1] if j + 1 < len(curve) else None

        cur_time = float(cur.get("time", 0.0))
        cur_value = float(cur.get("value", 0.0))

        prev_time = float(prev.get("time", 0.0))
        prev_value = float(prev.get("value", 0.0))

        in_slope = cur.get("inSlope", 0.0)
        out_slope = prev.get("outSlope", 0.0)

        # 字符串 Infinity -> float
        if isinstance(in_slope, str):
            if in_slope == "Infinity":
                in_slope = math.inf
            else:
                in_slope = float(in_slope)

        if isinstance(out_slope, str):
            if out_slope == "Infinity":
                out_slope = math.inf
            else:
                out_slope = float(out_slope)

        in_slope = float(in_slope)
        out_slope = float(out_slope)

        # --------------------------------------------------
        # InverseStepped
        # --------------------------------------------------

        if (
            abs(cur_time - prev_time - 0.01) < 0.0001
            and next_curve is not None
            and float(next_curve.get("value", 0.0)) == cur_value
        ):
            segments.append(3)

            segments.append(float(next_curve.get("time", 0.0)))
            segments.append(float(next_curve.get("value", 0.0)))

            j += 2
            continue

        # --------------------------------------------------
        # Stepped
        # --------------------------------------------------

        if math.isinf(in_slope) and in_slope > 0:
            segments.append(2)

            segments.append(cur_time)
            segments.append(cur_value)

            j += 1
            continue

        # --------------------------------------------------
        # Linear
        # --------------------------------------------------

        if (
            out_slope == 0.0
            and abs(in_slope) < 0.0001
            and not force_bezier
        ):
            segments.append(0)

            segments.append(cur_time)
            segments.append(cur_value)

            j += 1
            continue

        # --------------------------------------------------
        # Bezier
        # --------------------------------------------------

        tangent_length = (cur_time - prev_time) / 3.0

        cx1 = prev_time + tangent_length
        cy1 = out_slope * tangent_length + prev_value

        cx2 = cur_time - tangent_length
        cy2 = cur_value - in_slope * tangent_length

        segments.append(1)

        segments.append(cx1)
        segments.append(cy1)

        segments.append(cx2)
        segments.append(cy2)

        segments.append(cur_time)
        segments.append(cur_value)

        j += 1

    return segments


def count_segments_from_segments(segments: list) -> int:
    """
    Count logical segments from a motion3 `Segments` array.
    """
    if not segments:
        return 0
    # pos = 0
    # first two entries are initial time/value
    pos = 2
    cnt = 0
    L = len(segments)
    while pos < L:
        seg_type = int(segments[pos])
        if seg_type == 0 or seg_type == 2 or seg_type == 3:
            # linear / stepped / inverse-stepped consume 3 entries (type,time,value)
            pos += 3
            cnt += 1
        elif seg_type == 1:
            # bezier consumes 7 entries (type, cx1, cy1, cx2, cy2, time, value)
            pos += 7
            cnt += 1
        else:
            # unknown, break to avoid infinite loop
            break
    return cnt

def count_points_from_segments(segments: list) -> int:
    """
    Count logical points from motion3 Segments.
    """
    if not segments:
        return 0
    cnt = 1  # 初始点
    pos = 2
    L = len(segments)
    while pos < L:
        seg_type = int(segments[pos])
        if seg_type in (0, 2, 3):
            cnt += 1
            pos += 3
        elif seg_type == 1:
            cnt += 3
            pos += 7
        else:
            break
    return cnt


def fade2json(path: str, output: str):
    # 1. 依次读取 {model_name}.fadeMotionList 文件, 根据其中的 "motionsData" > "m_PathID" 生成一个字典 dict[pathID] = model_name
    input_dir = Path(path)
    output_dir = Path(output)
    if not input_dir.exists():
        raise FileNotFoundError(f"输入目录不存在: {input_dir}")

    id_model_cache: dict[str, str] = {} # dict[pathID] = model_name

    fmls = list(input_dir.glob("*.fadeMotionList @*.json"))
    for fml in fmls:
        try:
            with open(fml, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not data:
                raise ValueError("JSON 为空")
            model_name = (data.get("m_Name") or fml.stem).split(".")[0]
            motions_data = data.get("motionsData", [])
            for motion in motions_data:
                path_id = str(motion.get("m_PathID"))
                if path_id:
                    id_model_cache[path_id] = model_name

        except Exception as e:
            print(f"[FAIL] {fml}: {e}")

    # 2. 预加载所有 moc3 参数, 避免重复解析 moc3 文件, 生成一个字典 dict[model_name] = params_list
    moc3_params_parts_cache: dict[str, tuple[list[str], list[str]]] = {} # dict[model_name] = (param_ids, part_ids)
    model_names = set(id_model_cache.values())
    for name in model_names:
        try:
            moc3_file = output_dir / name / f"{name}.moc3"
            if not moc3_file.exists():
                raise FileNotFoundError(f"moc3 文件不存在: {moc3_file}")
            params, parts = extract_params_parts(moc3_file)

            if not params:
                raise ValueError("未提取到参数列表")
            if not parts:
                raise ValueError("未提取到部件列表")

            moc3_params_parts_cache[name] = (params, parts)
        except Exception as e:
            print(f"[FAIL] moc3 preload {name}: {e}")

    # 3. 解析 FADE_PATH 下的所有 {motion_name}.fade @{pathID}.json, 根据其中的 ControlIds 列表和 moc3 中的参数列表还原出参数名, 转换为 .motion3.json
    # 根据这个字典找到对应的模型名, 输出为 OUTPUT_PATH\{model_name}\motions\{motion_name}.motion3.json
    fades = list(input_dir.glob("*.fade @*.json"))
    for fade in fades:
        try:
            with open(fade, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not data:
                raise ValueError("JSON 为空")

            control_ids = data.get("ControlIds", [])
            curves = data.get("ControlTracks", [])
            motion_name = str(data.get("m_Name")).split(".")[0]

            if len(control_ids) == 0 or len(curves) == 0:
                print(f"[WARN] ControlIds 或 ControlTracks 为空, 已跳过 {fade}")
                continue

            path_id = fade.stem.split("@")[-1].strip()
            model_name = id_model_cache.get(path_id)
            params_parts_tuple = moc3_params_parts_cache.get(model_name)

            if not params_parts_tuple:
                raise ValueError(f"未找到 moc3 参数缓存: {model_name}")
            else:
                params, parts = params_parts_tuple



            # build mapping for each control id -> (target, id)
            control_map: list[tuple[str, str] | None] = []
            for idx in control_ids:
                idx = int(idx)
                if idx < len(params):
                    control_map.append(("Parameter", params[idx]))
                else:
                    part_idx = idx - len(params)
                    if part_idx < len(parts):
                        control_map.append(("PartOpacity", parts[part_idx]))
                    else:
                        # unknown id, append None to keep indices aligned
                        print(f"[WARN] ControlId {idx} out of range for model {model_name}")
                        control_map.append(None)

            # 构建 motion3.json
            motion3_json = {
                "Version": 3,
                "Meta": {
                    "Duration": 0.0,
                    "Fps": 60.0,
                    "Loop": True,
                    "AreBeziersRestricted": True,
                    "CurveCount": 0,
                    "TotalSegmentCount": 0,
                    "TotalPointCount": 0,
                    "UserDataCount": 0,
                    "TotalUserDataSize": 0
                },
                "Curves": [],
                "UserData": []
            }
            total_segment_count = 0
            total_point_count = 0
            duration = float(data.get("MotionLength", 0.0))

            for i, curve_obj in enumerate(curves):
                curve = curve_obj.get("m_Curve", [])

                segments = convert_segments(curve)

                seg_cnt = count_segments_from_segments(segments)
                total_segment_count += seg_cnt
                point_cnt = count_points_from_segments(segments)
                total_point_count += point_cnt


                # map control -> curve by index
                if i < len(control_map) and control_map[i] is not None:
                    target, cid = control_map[i]
                    motion3_json["Curves"].append({
                        "Target": target,
                        "Id": cid,
                        "Segments": segments
                    })
                else:
                    # no mapping for this curve; skip
                    print(f"[WARN] no control mapping for curve index {i} in {fade}")
                    continue



            motion3_json["Meta"]["CurveCount"] = len(motion3_json["Curves"]) 
            motion3_json["Meta"]["Duration"] = duration
            motion3_json["Meta"]["TotalSegmentCount"] = total_segment_count
            motion3_json["Meta"]["TotalPointCount"] = len(motion3_json["Curves"]) + total_segment_count

            out_path = output_dir / model_name / "motions" / f"{motion_name}.motion3.json"
            out_path.parent.mkdir(parents=True, exist_ok=True)

            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(motion3_json, f, ensure_ascii=False, indent=4)
            print(f"[OK] {fade} -> {out_path}")

        except Exception as e:
            print(f"[FAIL] {fade}: {e}")

def read_int32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset+4], "little", signed=True)
def read_int64(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset+8], "little", signed=True)
def read_string(data: bytes, offset: int, length: int) -> str:
    return data[offset:offset+length].decode("utf-8")

def extract_meta_info(meta_path: str) -> dict[str,tuple[str, int]]:
    # 解析二进制数据
    # 结构如下:
    # int name_len //4B
    # char bundle_name[name_len] // name_len B
    # 对齐4个字节 align 4B
    # int preload_size //4B
    # struct {
    #     int file_id //4B
    #     int64 path_id //8B little-end
    # } preload[preload_size]
    #
    # int container_size //4B
    # struct {
    #     int hash_len //4B
    #     char hash[hash_len] //hash_len B
    #     对齐4个字节 align 4B
    #     int preloadIndex //4B
    #     int preloadSize //4B
    #     int file_id //4B
    #     int64 path_id //8B
    # } container[container_size]
    # //...后面的没什么用

    id_model_cache: dict[str,tuple[str, int]] = {} # dict[pathID] = (model_name, resolution)
    # 生成一个字典 dict[model_name] = [texture_id1, texture_id2, ...]
    # model_name 从 bundle_name中 提取, 如
    # assets/art_live2d_cg_kvn9n103_kvn9n103.4096.bundle 则 model_name = kvn9n103
    # assets/art_live2d_characters_adela_2_adela_2.2048.bundle 则 model_name = adela_2
    # texture_id 使用 container[] 中所有的的 path_id 表示
    for dat in Path(meta_path).rglob("*.dat"):
        try:
            with open(dat, "rb") as f:
                data = f.read()
            if not data:
                raise ValueError("文件为空")

            offset = 0
            name_len = read_int32(data, offset); offset += 4
            bundle_name = read_string(data, offset, name_len); offset += name_len
            match = re.search(r'_(.+?)_\1\.(1024|2048|4096)\.', bundle_name)
            if not match:
                raise ValueError(f"bad regex")
            model_name = match.group(1)
            resolution = int(match.group(2))

            # 对齐4B
            offset = (offset + 3) & ~3

            preload_size = read_int32(data, offset); offset += 4
            for _ in range(preload_size):
                _file_id = read_int32(data, offset); offset += 4
                _path_id = read_int64(data, offset); offset += 8

            container_size = read_int32(data, offset); offset += 4
            for _ in range(container_size):
                hash_len = read_int32(data, offset); offset += 4
                _hash_str = read_string(data, offset, hash_len); offset += hash_len
                # 对齐4B
                offset = (offset + 3) & ~3

                _preload_index = read_int32(data, offset); offset += 4
                _preload_size = read_int32(data, offset); offset += 4
                _file_id = read_int32(data, offset); offset += 4
                path_id = read_int64(data, offset); offset += 8

                id_model_cache[str(path_id)] = (model_name, resolution)

            # print(f"[OK] {dat} -> model: {model_name}  textures: {container_size}")

        except Exception as e:
            print(f"[FAIL] {dat}: {e}")

    # print(f"{id_model_cache}")
    return id_model_cache

def sort_textures_by_meta(meta_path: str, textures_path: str, output_path: str):
    id_model_cache = extract_meta_info(meta_path)  # dict[pathID] = model_name

    # 然后从 textures_path 目录中找到对应的纹理文件, 纹理文件命名格式如 texture_00 @45172633618687165.png, @后面是 path_id
    # 根据这个 path_id 就可以找到对应的纹理文件, 找到后就移动到 output_path\{model_name}\textures\ 目录下, 删除@和后面的 path_id, 注意strip
    for tex in Path(textures_path).glob("*.png"):
        try:
            match = re.search(r'@(-?\d+)', tex.stem)
            if not match:
                raise ValueError("文件名格式不正确, 无法提取 path_id")
            path_id = match.group(1)
            model_info = id_model_cache.get(path_id)
            if not model_info:
                raise ValueError(f"未找到对应的模型信息: {path_id}")
            model_name = model_info[0]
            resolution = model_info[1]

            # 首字母改为大写, 以匹配 moc3 文件夹的命名
            model_name = model_name[0].upper() + model_name[1:] if model_name else None

            out_dir = Path(output_path) / model_name / "textures"
            out_dir.mkdir(parents=True, exist_ok=True)

            # 有一个疑问： 如果存在同一个模型的多分辨率纹理, 比如2048和4096, 有没有可能2048会用2个纹理
            # 4096只用1个纹理, 这样就会出现重名的情况, 导致后面一个覆盖前面一个, 这里选择额外命名
            clear_name = tex.stem.split('@')[0].strip()
            out_path = out_dir / f"{clear_name}_{resolution}.png"
            if out_path.exists():
                print(f"多分辨率的模型 MOC3: {model_name}.moc3")
                # raise FileExistsError(f"目标文件已存在: {out_path}, 可能是多分辨率的模型")
            tex.rename(out_path)
            # print(f"[OK] {tex} -> {out_path}")
        except Exception as e:
            print(f"[FAIL] {tex}: {e}")

def main():
    if not os.path.exists(ROOT_DIR):
        raise FileNotFoundError(f"根目录不存在: {ROOT_DIR}")
    init_live2d_core()

    # 1. 将 MOC3_JSON_PATH 目录下的 json 文件转换为 moc3 文件
    # 输出为 OUTPUT_PATH\{model_name}\{model_name}.moc3
    json2moc3(MOC3_JSON_PATH, OUTPUT_PATH)

    # 2. 将 FADE_PATH 目录下的 {motion_name}.fade @{pathID}.json 文件转换为 .motion3.json 文件
    # 输出为 OUTPUT_PATH\{model_name}\motions\{motion_name}.motion3.json
    fade2json(FADE_PATH, OUTPUT_PATH)

    # 3. 根据 TEXTURES_META_PATH 目录下的 .dat 文件解析出纹理对应的模型信息,
    # 然后将 TEXTURES_PATH 目录下的纹理文件移动到 OUTPUT_PATH\{model_name}\textures\ 目录下
    # 并重命名为 {texture_name}_{resolution}.png
    sort_textures_by_meta(TEXTURES_META_PATH, TEXTURES_PATH, OUTPUT_PATH)

if __name__ == "__main__":
    main()