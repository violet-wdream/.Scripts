# 5fb3ffbe6a0ecfa290f72b0347f7cda7 是 pathlist 文件的名字，里面是一个树状结构的目录和文件列表

from __future__ import annotations
import hashlib
import json
import orjson
import csv
from pathlib import Path


def read_cstr(data: bytes, pos: int) -> tuple[str, int]:
    """读取一个以 \\x00 结尾的字符串，返回 (字符串, 下一个位置)"""
    end = data.index(0, pos)
    return data[pos:end].decode('utf-8'), end + 1

def parse_node(data: bytes, pos: int) -> tuple[dict, int]:
    """递归解析一个节点（目录或文件），返回 (节点dict, 下一个位置)"""
    name, pos = read_cstr(data, pos)

    if name.endswith('/'):
        # 目录节点：递归读子节点，直到遇到单独的 0x00 结束标记
        children = []
        while data[pos] != 0:
            child, pos = parse_node(data, pos)
            children.append(child)
        pos += 1  # 跳过子节点列表的结束符 0x00
        return {'type': 'dir', 'name': name, 'children': children}, pos
    else:
        # 文件节点：名字后面跟 4 字节未知数据
        if pos + 4 > len(data):
            raise ValueError(f"文件在解析 '{name}' 的大小字段时意外截断 (pos={pos})")
        # size = struct.unpack_from('<f', data, pos)[0]
        dat = data[pos:pos+4].hex()
        pos += 4
        return {'type': 'file', 'name': name, '4Bdat': dat}, pos


def parse_namelist(data: bytes) -> list[dict]:
    """解析整个文件，返回顶层节点列表"""
    pos = 0
    n = len(data)
    top_nodes = []
    while pos < n:
        node, pos = parse_node(data, pos)
        top_nodes.append(node)

    return top_nodes

def collect_names(nodes):
    result = []
    for node in nodes:
        if node["type"] == "dir":
            result.extend(collect_names(node["children"]))
        else:
            result.append(node["name"])
    return result

def md5_hash(s):
    return hashlib.md5(s.encode()).hexdigest()

def flatten(nodes: list[dict], prefix: str = '') -> list[tuple[str, str, str]]:
    """把树状结构展平成 (完整路径, 4Bdat, path_md5) 的列表"""
    result = []
    for node in nodes:
        full = prefix + node['name']
        if node['type'] == 'dir':
            result.extend(flatten(node['children'], full))
        else:
            path_md5 = md5_hash(full)
            result.append((full, node['4Bdat'], path_md5))
    return result



def main():
    pathlist = Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\DaoYou\5fb3ffbe6a0ecfa290f72b0347f7cda7")
    if not pathlist.exists():
        raise FileNotFoundError(f"文件 {pathlist} 不存在")

    data = pathlist.read_bytes()
    top_nodes = parse_namelist(data)
    flat = flatten(top_nodes)
    names = collect_names(top_nodes)

    print(f"解析完成：顶层节点 {len(top_nodes)} 个，文件总数 {len(flat)} 个，"
          f"字节数 {len(data)}")

    # 输出 JSON
    # out_json = Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\DaoYou\namelist.json")
    # out_json.write_bytes(
    #     orjson.dumps(top_nodes)
    # )
    # print(f"已写入 JSON 文件 {out_json}")

    # 输出 TXT
    # out_txt = Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\DaoYou\namelist.txt")
    # out_txt.write_text(
    #     '\n'.join(names),
    #     encoding='utf-8'
    # )
    # print(f"已写入 TXT 文件 {out_txt}")


    out_csv = Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\DaoYou\pathlist.csv")
    with out_csv.open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['path', '4Bdat', 'path_md5'])
        w.writerows(flat)
    print(f"已写入 CSV 文件 {out_csv}")

if __name__ == "__main__":
    main()
