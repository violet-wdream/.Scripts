执行默认在  脚本当前目录以及根目录下

1. AtlasPngResize：将atlas文件需要的png图片尺寸调节到所需的尺寸。
2. DecryptPng(DAT_0180ac00-UF-Echocalypse)： 绯色回响图片加密处理（图片16进制打开有UF关键字），需要先下载TexturePacker（激活），然后加入到环境变量，通过将加密的png图片转换为.pvr.ccz文件再用TexturePacker转换回png。
3. DecryptXOR/DecryptXORTest： 功能一致，Test是前者的完全版，检测Bundle文件的异或加密种类，可以尝试更多种类的XOR加密，用于处理unity资源的XOR加密。
4. DelEmptyDirs：删除所有空的目录
5. DelSufFiles(.pvr.ccz+...)：删除特定后缀的文件，可自定义
6. ProcessModel3(ForAzurLane)：个人使用的脚本，用于展示碧蓝航线的L2D
7. ProcessModel3ByMotion3： 通过motions目录下的动作（自动修改为.motion3.json后缀）来补充model3配置，如果没有model3则会生成，所以也可以用于生成model3文件。
8. SortAtlas&Skel&png(Any)：如果所有的atlas和skel等等文件混在了一起，会根据atals文件的名称作为模型名称创建一个目录，再把同名（同前缀）的其他纹理图/骨骼分类到这个目录下。
9. SortAtlas&Skel&png(AzurLane)：个人使用的脚本，只不过是指定了目录而已。
10. DelDirSuf(.unity3d_export)&MvCAB：删除所有的目录特定后缀（.unity3d_export），可自定义，同时将下一级CAB目录的内容移到上一级。
11. DelDirSuf(_res_export)&MvCAB：同理
12. DelErrorEmptyDir(Drag File)：有时候会莫名生成空的目录，然后删不掉，就把目录拖到这个bat上删除
13. DelFileSuf(.asset)：删除所有文件的后缀.asset
14. DelFileSuf(.prefab)：同理删除所有文件的后缀.prefab

