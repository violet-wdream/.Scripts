import os, sys

DAT_0180ac00 = [19, 91, 12, 13, 102, 22, 34, 43, 17, 25, 88, 64, 36, 16, 14, 66,
                49, 87, 56, 44, 53, 28, 11, 5, 116, 37, 58, 105, 20, 15, 77, 7, 29,
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 19, 91, 12, 13, 102, 22,
                34, 43, 17, 25, 88, 64, 36, 16, 14, 66, 49, 87, 56, 44, 53, 28, 11, 5,
                116, 37, 58, 105, 20, 15, 77, 7, 29, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                0, 0, 0]

for subdir, dirs, files in os.walk(os.getcwd()):
    for file in files:
        # print os.path.join(subdir, file)
        filepath = subdir + os.sep + file

        if filepath.endswith(".png"):

            t = open(filepath, "rb").read()
            t = bytearray(t)

            if (t[0] == 85) and (t[1] == 70):  # U and F
                size = len(t)
                k = t.copy()
                off = 5
                b = t[4]
                if (t[size - 13] == 73) and (t[size - 12] == 69):

                    # for i in range(off):
                    # k[i] = t[size - off + i] ^ DAT_0180ac00[b + i]
                    k[0] = 137
                    k[1] = 80
                    k[2] = 78
                    k[3] = 71
                    k[4] = 13

                else:
                    k[0] = 67
                    k[1] = 67
                    k[2] = 90
                    k[3] = 33
                    k[4] = 0

                for i in range(off, min(0x64, size)):
                    k[i] = k[i] ^ DAT_0180ac00[(i + b) % 0x21]

                open(filepath, "wb").write(k)

                if (k[0] == 67) and (k[1] == 67):

                    base_file, ext = os.path.splitext(filepath)
                    if ext == ".png":
                        os.rename(filepath, base_file + ".pvr.ccz")

for subdir, dirs, files in os.walk(os.getcwd()):
    for file in files:
        # print os.path.join(subdir, file)
        filepath = subdir + os.sep + file
        ext = filepath.split('.')
        newpath = ext[0] + '.png'
        ext2 = ext[1]

        print(filepath)
        if ext2 == "pvr":
            command = "cmd /c TexturePacker" + " " + filepath + " " + "--sheet" + " " + newpath + " --data dummy.plist --algorithm Basic --allow-free-size --no-trim --max-size 102400"
            print(command)

            os.system(command)