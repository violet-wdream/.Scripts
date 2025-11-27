import os
# 将当前工作目录设置为脚本所在目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))



total_bundles = 0
success_count = 0
error_count = 0


def decrypt_and_save(file_path):
    global total_bundles, success_count, error_count
    total_bundles += 1
    print(file_path)
    with open(file_path, "rb") as f:
        data = f.read()
    result = bytearray(data)[50:]
    key = result[0] ^ 0x55  # U
    if key != result[1] ^ 0x6E:  # n
        print("Decryption Error: Not an Unity File!")
        error_count += 1
    else:
        result = [byte ^ key for byte in result]
        decrypted_file_path = file_path + ".decr"
        with open(decrypted_file_path, "wb") as f:
            f.write(bytes(result))
        success_count += 1


if __name__ == "__main__":
    for root, dirs, files in os.walk(os.getcwd()):
        for file in files:
            if file.endswith(".bundle"):
                decrypt_and_save(os.path.join(root, file))
    print(f"\nDecryption completed. {total_bundles} in total, {success_count} successful, {error_count} failed.")
    input("Press Enter to exit ...")
