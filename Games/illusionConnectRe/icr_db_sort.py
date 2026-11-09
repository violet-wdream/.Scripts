from pathlib import Path
import sqlite3
import shutil


def restore_assets(source_dir: Path, output_dir: Path, db_path: Path, table_name: str = "assets", ):
    conn = sqlite3.connect(db_path)

    try:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT real, logic
            FROM {table_name}
        """)
        count = 0
        false_count = 0
        
        for realpath, logicpath in cursor.fetchall():
            if not realpath or not logicpath:
                continue
            source = source_dir / realpath
            target = output_dir / logicpath
            if not source.exists():
                false_count += 1
                # print(f"[不存在] {source}, logic {target}")
                continue

            target.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(source, target)

            # print(f"[恢复] {realpath} -> {logicpath}")
            count += 1
        print(f"\n完成，共恢复 {count} 个文件")
        print(f"miss {false_count}")
    finally:
        conn.close()


if __name__ == "__main__":
    ASSETS_DB_PATH = Path(r"data\assets.db")
    EXTENSIONS_DB_PATH = Path(r"data\extensions.db")
    SOURCE_DIR = Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\illusionConnectRe")
    OUTPUT_DIR = Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\illusionConnectRe\extract")
    
    print("=== Assets ===")
    restore_assets(
        SOURCE_DIR,
        OUTPUT_DIR,
        ASSETS_DB_PATH,
        table_name="assets"
    )

    print("=== Extensions ===")
    restore_assets(
        SOURCE_DIR,
        OUTPUT_DIR,
        EXTENSIONS_DB_PATH,
        table_name="extension"
    )