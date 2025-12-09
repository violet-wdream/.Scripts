import requests
import lz4.frame
import os


def fetch_abfiles_binary():
    url_version = (
        "https://fx-plat-fzsnweb.c4games.com/common/script/clientVersion"
        "?deviceId=&gameId=15&platform=webdesk&branch=webgl-release"
    )
    r = requests.get(url_version, timeout=10)
    r.raise_for_status()
    info = r.json()

    br = info["br"]
    ab = info["ab"]

    base = (
        "https://sf-snh5.bytedgame.com/obj/youai-c10-cdn-sg/"
        "gdl_app_302906/game/webgl/webgl-release/Desktop/"
    )

    abfiles_url = f"{base}{br}/abfiles{ab}"

    r2 = requests.get(abfiles_url, timeout=10)
    r2.raise_for_status()

    return abfiles_url, lz4.frame.decompress(r2.content)  # return URL+data


if __name__ == "__main__":
    url, data = fetch_abfiles_binary()

    # 获取原始文件名
    raw_filename = os.path.basename(url)   # 如 abfiles123456
    output_name = raw_filename + ".txt"    # abfiles123456.txt

    with open(output_name, "wb") as f:
        f.write(data)

    print(f"已保存: {output_name}")
