执行默认在  脚本当前目录以及根目录下，自动搜索对应文件，理论上只需要执行而不需要添加参数。

为了防止意外，请先使用少量文件进行实验并备份源文件。

## Decrypt

1. `DecryptPng(DAT_0180ac00-UF-Echocalypse)`： 绯色回响 图片加密处理（图片16进制打开有UF关键字），需要先下载TexturePacker（激活），然后加入到**环境变量**，通过将加密的png图片转换为.pvr.ccz文件再用TexturePacker转换回png。
2. `DecryptXOR`/`DecryptXORTest`： 功能一致，Test是前者的完全版，检测Bundle文件的异或加密种类，可以尝试更多种类的XOR加密，用于处理unity资源的XOR加密。
3. `Decrypt64B-XOR(GirlsLoveDance)`：处理 千娇百媚 的文件前64个字节XOR加密
4. `WPKUnpacker.py`：解密WPK文件，通常会得到LPK、config、png；调用了本地bandizip进行解压，使用了bandizip6.29的bc.exe命令行工具，高级版本为bz.exe，需要把bc添加到环境变量
5. `LPKUnpacker.py`：解密LPK文件，需要配合config.json文件一起使用；支持Live2D和Spine 
6. `YooAssetUnpacker.py`：用于处理Unity的YooAsset资产框架解密。经典目录结构就是Package目录下有ManifestFiles和CacheBundleFiles，处理完之后就是正常的unity文件
7. 

## DestinyChild

处理天命之子的导出文件

1. `ProcessDC.py` ：大致进行以下处理，以目录c000_01为例
   1. character.dat 名称修改为 name.moc (c000_01.moc)
   2. MOC.name.json 名称修改为 name.model.json (c000_01.model.json)
   3. MOC.name.json 内容中model键的值修改为对应moc文件名称 ( "model": "c000_01.moc", )
2. 

## Live2DFileConvert

不推荐自行处理L2D文件，推荐使用Mod版本L2D一键导出

1. `Fade2Motion3(noHash).js`：将fade.json文件处理为motion3.json文件，需要本地node环境

   ```js
   node Fade2Motion3(noHash).js
   ```

2. `Json2Moc3.py`：将json形式的moc3文件转换为二进制的moc3文件，原理是拼接了json里面的`_bytes`字段，所以json里面必须有这个字段

3. `ProcessModel3ByMotion3.py`：处理model3配置文件，确保model3中一定有动作。不同环境下model3格式略有不同，比如经典的`hitAreas` 字段

4. `ProcessModel3(ForAzurLane).py`：个人使用的工具，功能同上。用来处理碧蓝的的模型配置model3

5. 

## Png

1. `AtlasPngResize.py`：根据atlas文件中的尺寸来调节实际png的尺寸。
2. ``

## Sort

1. `SortAtlas&Skel&png(Any).py`：如果所有的atlas和skel等等文件混在了一起，会根据atals文件的名称作为模型名称创建一个目录，再把同名（同前缀）的其他纹理图/骨骼分类到这个目录下。
2. `SortAtlas&Skel&png(AzurLane).sh`：个人使用的脚本，只不过是指定了目录而已。
3. 



## Other

1. `AddFileSuf(.json).py`：给所有无拓展名文件添加json后缀。

2. `DelEmptyDirs.py`：删除所有空的目录

3. `DelEmptyParDirs.py`：删除所有“空”父级目录，如果父级只有一个子级目录就会被子级目录“取代”，不是很稳定，不建议使用。

4. `DelFakeHeader.py`： 删除FakeHeader。

5. `DelOtherModelJson (LPKAssets).py`: 有的LPK解压后的模型会有很多model.json实际上只需要保留和atals匹配的model.json即可。用于处理战姬收藏的LPK解包。

6. `DelSufFiles(.pvr.ccz+...).py`：删除特定后缀的文件，可自定义

7. `ExtractSecondaryFiles.py`：提取脚本目录的其他目录的所有递归子目录文件，注意脚本放置的位置！！！

   ```
   Before:
   根目录/
     ├─ 项目A/
     │   ├─ 源代码/
     │   │   ├─ main.py
     │   │   └─ utils.py
     │   └─ 文档/
     │       └─ readme.txt
     └─ 项目B/
         ├─ src/
         │   └─ app.js
         └─ assets/
             └─ image.jpg
   After:
   根目录/
     ├─ 项目A/
     │   ├─ main.py
     │   ├─ utils.py
     │   └─ readme.txt
     └─ 项目B/
         ├─ app.js
         └─ image.jpg
   ```

   

8. `DelDirSuf(.unity3d_export)&MvCAB`：删除所有的目录特定后缀（.unity3d_export），可自定义，同时将下一级CAB目录的内容移到上一级。

9. `DelDirSuf(_res_export)&MvCAB`：同理。

10. `DelErrorEmptyDir(Drag File)`：有时候会莫名生成空的目录，然后删不掉，就把目录拖到这个bat上删除，注意：这个删除方式不会放到回收站。

11. `DelFileSuf(.asset)`：删除所有文件的后缀.asset

12. `DelFileSuf(.prefab)`：同理删除所有文件的后缀.prefab

13. 

