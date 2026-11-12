"""Convert Unity AnimationClip curves to Live2D motion3.json data."""
from __future__ import annotations

import math
import re
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path

CRC_VALUE = zlib.crc32(b"Value") & 0xFFFFFFFF
CRC_OPACITY = zlib.crc32(b"Opacity") & 0xFFFFFFFF


@dataclass
class Key:
    time: float
    value: float
    coeff: tuple[float, float, float, float] | None = None
    in_slope: float = 0.0
    out_slope: float = 0.0


def build_moc3_maps(moc3_path: Path, targets: set[int] | None = None):
    """
    CRC32(path_hash) -> parameter/part id, using the MOC3 string table.
    If targets is given, only those path hashes are decoded/stored, which is
    much faster when a model only animates a few hundred properties.
    """
    
    raw = moc3_path.read_bytes()
    param_prefix = zlib.crc32(b"Parameters/")
    part_prefix = zlib.crc32(b"Parts/")
    
    params, parts = {}, {}
    for match in re.finditer(rb"[\x20-\x7e]{2,}", raw):
        value = match.group()
        param_hash = zlib.crc32(value, param_prefix) & 0xFFFFFFFF
        part_hash = zlib.crc32(value, part_prefix) & 0xFFFFFFFF
        want_param = targets is None or param_hash in targets
        want_part = targets is None or part_hash in targets
        if not (want_param or want_part):
            continue
        text = value.decode("ascii")
        if want_param:
            params.setdefault(param_hash, text)
        if want_part:
            parts.setdefault(part_hash, text)
    return params, parts


def _next_in_slope(previous: Key, current: Key, dt: float) -> float:
    """Port of AssetStudio StreamedCurveKey.CalculateNextInSlope."""
    coeff = previous.coeff
    if coeff is None:
        return 0.0
    if coeff[0] == 0.0 and coeff[1] == 0.0 and coeff[2] == 0.0:
        return 0.0
    dt = max(dt, 0.0001)
    dy = current.value - previous.value
    length = 1.0 / (dt * dt)
    d1 = previous.out_slope * dt
    d2 = dy + dy + dy - d1 - d1 - coeff[1] / length
    return d2 / dt


def _read_streamed(clip) -> dict[int, list[Key]]:
    streamed = clip.m_StreamedClip
    data = list(streamed.data or [])
    if not data:
        return {}

    raw = b"".join(struct.pack("<I", value & 0xFFFFFFFF) for value in data)
    frames, offset = [], 0
    while offset + 8 <= len(raw):
        time, count = struct.unpack_from("<fi", raw, offset)
        offset += 8
        if count < 0 or count > 100000:
            break
        keys = []
        for _ in range(count):
            if offset + 20 > len(raw):
                break
            index = struct.unpack_from("<i", raw, offset)[0]
            coeff = struct.unpack_from("<4f", raw, offset + 4)
            offset += 20
            keys.append((index, Key(time, coeff[3], coeff, 0.0, coeff[2])))
        if math.isfinite(time) and time > -1e30:
            frames.append((time, {index: key for index, key in keys}))

    result: dict[int, list[Key]] = {}
    for _, keys in frames:
        for index, key in keys.items():
            result.setdefault(index, []).append(key)

    # Compute incoming slopes from the previous key of the same curve.
    for frame_index in range(1, len(frames)):
        time, keys = frames[frame_index]
        for index, key in keys.items():
            for previous_index in range(frame_index - 1, -1, -1):
                previous_time, previous_keys = frames[previous_index]
                previous = previous_keys.get(index)
                
                if previous is not None:
                    key.in_slope = _next_in_slope(previous, key, time - previous_time)
                    break
    return result


def _read_dense(clip, start: int) -> dict[int, list[Key]]:
    dense = clip.m_DenseClip
    samples = list(dense.m_SampleArray or [])
    if dense.m_CurveCount <= 0 or dense.m_FrameCount <= 0 or not samples:
        return {}

    result: dict[int, list[Key]] = {}
    for frame in range(dense.m_FrameCount):
        time = dense.m_BeginTime + frame / dense.m_SampleRate
        base = frame * dense.m_CurveCount
        for curve in range(dense.m_CurveCount):
            position = base + curve
            if position < len(samples):
                result.setdefault(start + curve, []).append(Key(time, samples[position]))
    return result


def _read_constant(clip, start: int, stop: float) -> dict[int, list[Key]]:
    return {
        start + index: [Key(0.0, value), Key(stop, value)]
        for index, value in enumerate(list(clip.m_ConstantClip.data or []))
        if math.isfinite(value)
    }


def _segments(keys: list[Key], duration: float):
    """Convert Unity Hermite keyframes to Cubism motion3 segments."""
    keys = sorted(
        (key for key in keys if math.isfinite(key.time) and math.isfinite(key.value)),
        key=lambda key: key.time,
    )
    if not keys:
        return None, 0, 0

    # Cubism starts with [startTime, startValue].
    segments = [round(keys[0].time, 4), round(keys[0].value, 5)]
    count = 0

    for j in range(1, len(keys)):
        current = keys[j]
        previous = keys[j - 1]
        dt = current.time - previous.time
        if dt <= 0:
            continue

        # Linear only when both tangents match the secant slope.
        secant = (current.value - previous.value) / dt
        if (abs(previous.out_slope - secant) < 1e-5
                and abs(current.in_slope - secant) < 1e-5):
            segments += [0, round(current.time, 4), round(current.value, 5)]
        else:
            # Cubic Bezier: 2 control points + endpoint.
            tangent = dt / 3.0
            segments += [
                1,
                round(previous.time + tangent, 4),
                round(previous.value + previous.out_slope * tangent, 5),
                round(current.time - tangent, 4),
                round(current.value - current.in_slope * tangent, 5),
                round(current.time, 4),
                round(current.value, 5),
            ]
        count += 1

    # Cubism Meta.TotalPointCount is the keyframe count, not the Bezier control-point count.
    return segments, count + 1, count


def animation_clip_to_motion(animation_clip, params: dict[int, str], parts: dict[int, str]) -> dict:
    muscle = animation_clip.m_MuscleClip
    duration = float(muscle.m_StopTime)
    clip = muscle.m_Clip.data if hasattr(muscle.m_Clip, "data") else muscle.m_Clip

    curves = {}
    curves.update(_read_streamed(clip))
    curves.update(_read_dense(clip, clip.m_StreamedClip.curveCount))
    curves.update(_read_constant(
        clip,
        clip.m_StreamedClip.curveCount + clip.m_DenseClip.m_CurveCount,
        duration,
    ))

    grouped: dict[tuple[str, str], list[Key]] = {}
    bindings = animation_clip.m_ClipBindingConstant.genericBindings
    for index, keys in curves.items():
        if index < 0 or index >= len(bindings):
            continue
        binding = bindings[index]
        if binding.path == 0 and binding.attribute == CRC_OPACITY:
            target, ident = "Model", "Opacity"
        elif binding.attribute == CRC_VALUE and binding.path in params:
            target, ident = "Parameter", params[binding.path]
        elif binding.attribute == CRC_OPACITY and binding.path in parts:
            target, ident = "PartOpacity", parts[binding.path]
        else:
            continue
        grouped.setdefault((target, ident), []).extend(keys)

    output = []
    total_points = 0
    total_segments = 0
    for (target, ident), keys in sorted(grouped.items()):
        segments, points, count = _segments(keys, duration)
        if segments:
            output.append({"Target": target, "Id": ident, "Segments": segments})
            total_points += points
            total_segments += count

    return {
        "Version": 3,
        "Meta": {
            "Duration": round(duration, 4),
            "Loop": True,
            "AreBeziersRestricted": True,
            "CurveCount": len(output),
            "Fps": 60.0,
            "TotalSegmentCount": total_segments,
            "TotalPointCount": total_points,
            "UserDataCount": 0,
            "TotalUserDataSize": 0,
        },
        "Curves": output,
        "UserData": [],
    }