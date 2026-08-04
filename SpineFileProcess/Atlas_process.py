# https://github.com/ww-rm/SpineViewer/blob/main/SpineRuntimes/SpineRuntime38/Atlas.cs
from pathlib import Path
from PIL import Image

INPUT_PATH = r"D:\Games\GameUnpackAssets\mymodel\Spine\IronSaga\Spine"
EXT = "atlas"
IMAGE_EXT = "png"
DRY_RUN = False

class RegionInfo:
    def __init__(self, name: str = "", rotate: bool = False, xy: tuple[int,int] = (0, 0),
                 size: tuple[int,int] = (0, 0), orig: tuple[int,int] = (0, 0),
                 offset: tuple[int,int] = (0, 0), index: int = 0):
        self.name = name
        self.rotate = rotate
        self.xy = xy
        self.size = size
        self.orig = orig
        self.offset = offset
        self.index = index

class PageInfo:
    def __init__(self, name: str = "", size: tuple[int,int] = (0,0),
                 fmt: str = "", ftr: tuple[str, str] = ("", ""), repeat: str = "",
                 regions: list[RegionInfo] = None):
        self.name = name
        self.size = size
        self.fmt = fmt
        self.ftr = ftr
        self.repeat = repeat
        self.regions = regions

    def get_region_by_name(self, name: str) -> RegionInfo | None:
        for region in self.regions:
            if region.name == name:
                return region
        print(f"Region {name} not found in page {self.name}")
        return None

    def set_name(self, name: str):
        self.name = name

    def set_size(self, size: tuple[int,int]):
        self.size = size

class AtlasInfo:
    def __init__(self, name: str, pages: list[PageInfo]):
        self.name = name
        self.pages = pages

    def get_page_by_name(self, page_name: str) -> PageInfo | None:
        for page in self.pages:
            if page.name == page_name:
                return page
        print(f"Page {page_name} not found in atlas")
        return None

    def get_page_by_index(self, index: int) -> PageInfo | None:
        if index < 0 or index >= len(self.pages):
            print(f"Page index {index} out of range")
            return None
        return self.pages[index]

    def get_page_names(self) -> list[str]:
        return [page.name for page in self.pages]

    def set_page_name(self, old_name: str, new_name: str):
        page = self.get_page_by_name(old_name)
        if page is not None:
            page.set_name(new_name)

    def set_index_page_name(self, index: int, new_name: str):
        page = self.get_page_by_index(index)
        if page is not None:
            page.set_name(new_name)

    def get_region_by_name(self, name: str) -> RegionInfo | None:
        for page in self.pages:
            region = page.get_region_by_name(name)
            if region is not None:
                return region
        print(f"Region {name} not found in atlas")
        return None

    def get_region_names(self) -> list[str]:
        names = []
        for page in self.pages:
            for region in page.regions:
                names.append(region.name)
        return names

def read_value(s: str) -> str:
    return s.split(":", 1)[1].strip()
def read_value_int(s: str) -> int:
    return int(read_value(s))

def read_tuple(s: str) -> tuple[str, str]:
    tup = read_value(s)
    a, b = tup.split(",")
    return a.strip(), b.strip()

def read_tuple_int(s: str) -> tuple[int, int]:
    a, b = read_tuple(s)
    return int(a), int(b)

def deserialize_atlas(atlas_name: str, text: str) -> AtlasInfo:
    lines = [line.replace('\r', '') for line in text.split('\n')]
    i: int = 0
    pages: list[PageInfo] = []

    while i < len(lines):
        line = lines[i].strip()
        if line.strip() == "":
            i += 1
            continue

        if ".png" in line or ".webp" in line:
            page_name: str = line.strip()
            i += 1

            size: tuple[int, int] = (0, 0)
            fmt: str = ""
            ftr: tuple[str, str] = ("", "")
            repeat: str = ""
            if "size" in lines[i]:
                size = read_tuple_int(lines[i])
                i += 1
            if "format" in lines[i]:
                fmt = read_value(lines[i])
                i += 1
            if "filter" in lines[i]:
                ftr = read_tuple(lines[i])
                i += 1
            if "repeat" in lines[i]:
                repeat = read_value(lines[i])
                i += 1

            regions: list[RegionInfo] = []
            while i < len(lines):
                line = lines[i]
                if line.strip() == "" or ".png" in line or ".webp" in line:
                    break  # 这页结束

                if ":" not in line:
                    region_name = line.strip()
                    i += 1

                    rot: bool = False
                    xy: tuple[int,int] = (0, 0)
                    size: tuple[int,int] = (0, 0)
                    orig: tuple[int,int] = (0, 0)
                    offset: tuple[int,int] = (0, 0)
                    index: int = 0

                    while i < len(lines) and ":" in lines[i]:
                        if "rotate" in lines[i]:
                            rot = read_value(lines[i]) == "true"
                            i += 1
                        if "xy" in lines[i]:
                            xy = read_tuple_int(lines[i])
                            i += 1
                        if "size" in lines[i]:
                            size = read_tuple_int(lines[i])
                            i += 1
                        if "orig" in lines[i]:
                            orig = read_tuple_int(lines[i])
                            i += 1
                        if "offset" in lines[i]:
                            offset = read_tuple_int(lines[i])
                            i += 1
                        if "index" in lines[i]:
                            index = read_value_int(lines[i])
                            i += 1

                        region = RegionInfo(
                            name=region_name, rotate=rot, xy=xy,
                            size=size, orig=orig,
                            offset=offset, index=index
                        )
                        regions.append(region)
                else:
                    i += 1
            page = PageInfo(
                name=page_name, size=size, fmt=fmt, ftr=ftr,
                repeat=repeat, regions=regions
            )
            pages.append(page)
    atlas_info = AtlasInfo(name=atlas_name, pages=pages)

    return atlas_info

def serialize_atlas(atlas: AtlasInfo) -> str:
    lines = []

    for p_idx, page in enumerate(atlas.pages):
        lines.append("")  # 不同的页之间用空行分割
        lines.append(f"{page.name.split('.')[0]}.{IMAGE_EXT}")
        lines.append(f"size: {page.size[0]},{page.size[1]}")  #注意这里,没有空格!!!
        lines.append(f"format: {page.fmt}")
        lines.append(f"filter: {page.ftr[0]},{page.ftr[1]}")  #注意这里,没有空格!!!
        lines.append(f"repeat: {page.repeat}")

        for region in page.regions:
            lines.append(region.name)
            lines.append(f"  rotate: {'true' if region.rotate else 'false'}")
            lines.append(f"  xy: {region.xy[0]}, {region.xy[1]}")
            lines.append(f"  size: {region.size[0]}, {region.size[1]}")
            lines.append(f"  orig: {region.orig[0]}, {region.orig[1]}")
            lines.append(f"  offset: {region.offset[0]}, {region.offset[1]}")
            lines.append(f"  index: {region.index}")

    return "\n".join(lines)

def reset_first_page_name(atlas: AtlasInfo, name: str = None):
    print(f"Resetting {atlas.name} first page name to {name if name else atlas.name}")
    first_page = atlas.get_page_by_index(0)
    if name is None: # 默认重置为 atlas 文件名
        name = atlas.name
    first_page.set_name(name)

def reset_first_page_size(atlas: AtlasInfo, size: tuple[int,int]):
    print(f"Resetting {atlas.name} first page size to {size}")
    if size[0] <= 0 or size[1] <= 0:
        print(f"Invalid size {size}, skipping")
        return
    first_page = atlas.get_page_by_index(0)
    first_page.set_size(size)

def is_targe_image_exist(path:Path, image_name: str) -> bool:
    images = path.rglob(f"{image_name}.png")
    return any(images)

def get_target_image_size(path:Path, image_name: str) -> tuple[int,int]:
    # 递归查找输入目录下的 指定名称图片, 找到就返回大小, 找不到就返回 (0, 0)
    for file in path.rglob(f"{image_name}.png"):
        try:
            with Image.open(file) as img:
                return img.size
        except Exception as e:
            print(f"Failed to open image {file}: {e}")
    print(f"Image {image_name} not found in {path}")
    return 0, 0

def main():
    for file in Path(INPUT_PATH).rglob(f"*.{EXT}"):
        text = file.read_text(encoding="utf-8", errors="ignore")
        atlas_info = deserialize_atlas(file.stem, text)

        # 这里可以对 atlas 进行修改

        # 1.把所有的atlas的第一页的名字重置为 atlas 文件名
        first_page = atlas_info.get_page_by_index(0)
        original_name = first_page.name
        reset_first_page_name(atlas_info)

        # 2.把所有的atlas的第一页的大小重置为输入目录下对应图片的大小
        target_size: tuple[int,int] = get_target_image_size(Path(INPUT_PATH), first_page.name)
        if target_size != (0, 0):
            reset_first_page_size(atlas_info, target_size)
        else: # 修改完第一页名字后 没有找到对应的图片, 恢复第一页名字
            reset_first_page_name(atlas_info, original_name)

        if not DRY_RUN:
            atlas_data = serialize_atlas(atlas_info)
            with file.open("w", encoding="utf-8") as f:
                f.write(atlas_data)


if __name__ == "__main__":
    main()