#!/bin/bash 

# === 配置 ===
SRC="$HOME/Desktop/mymodel/Azurlane/spinepainting"
DRYRUN=0  # 1 = dry-run，仅显示，不移动；0 = 执行移动

cd "$SRC" || exit
shopt -s nullglob

files_to_move=()

# 扫描现有目录
existing_dirs=()
for d in */; do
    existing_dirs+=("${d%/}")  # 去掉末尾的 /
done

# 扫描 atlas 文件
atlas_files=(*.atlas)

if [ ${#atlas_files[@]} -gt 0 ]; then
    # 存在 atlas 文件，创建目录并归类
    for atlas in "${atlas_files[@]}"; do
        name="${atlas%.atlas}"
        echo "[DEBUG] detected atlas: $name"

        if [ ! -d "$name" ]; then
            echo "[DEBUG] creating folder: $name/"
            [ "$DRYRUN" -eq 0 ] && mkdir "$name"
        fi

        # 前缀匹配或包含 atlas 名称
        for f in "$name"*.*; do
            [ -e "$f" ] || continue
            files_to_move+=("$f -> $name/")
        done
        for f in *"$name"*.*; do
            [ -e "$f" ] || continue
            files_to_move+=("$f -> $name/")
        done
    done
else
    # 没有 atlas 文件，尝试归类非目录文件到已有目录
    echo "[DEBUG] 未找到 atlas 文件，尝试归类非目录文件..."
    for f in *.*; do
        [ -f "$f" ] || continue
        fname="${f%.*}"      # 去掉扩展名
        fname="${fname%%#*}" # 去掉 # 及之后部分

        # 尝试匹配现有目录
        matched_dir=""
        for d in "${existing_dirs[@]}"; do
            if [[ "$fname" == "$d"* ]]; then
                matched_dir="$d"
                break
            fi
        done

        if [ -n "$matched_dir" ]; then
            files_to_move+=("$f -> $matched_dir/")
        fi
    done
fi

# === 列出清单 ===
if [ ${#files_to_move[@]} -eq 0 ]; then
    echo "没有找到需要移动的文件。"
    exit 0
fi

echo "以下文件将被移动："
printf "%s\n" "${files_to_move[@]}"

# === 用户确认 ===
read -p "确认执行移动操作？(y/N) " confirm
if [[ "$confirm" =~ ^[Yy]$ ]]; then
    for move_entry in "${files_to_move[@]}"; do
        src_file="${move_entry%% -> *}"
        dest_dir="${move_entry##* -> }"
        echo "[DEBUG] mv \"$src_file\" -> \"$dest_dir\"/"
        [ "$DRYRUN" -eq 0 ] && mv "$src_file" "$dest_dir"/
    done
    echo "[DEBUG] 移动完成。"
else
    echo "操作已取消。"
fi
