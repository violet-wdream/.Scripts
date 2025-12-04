执行默认在  脚本当前目录以及根目录下，自动搜索对应文件，理论上只需要执行而不需要添加参数。

为了防止意外，请先使用少量文件进行实验并备份源文件。

## Decrypt

1. `DecryptPng(DAT_0180ac00-UF-Echocalypse).py`： 绯色回响 图片加密处理（图片16进制打开有UF关键字），需要先下载TexturePacker（激活），然后加入到**环境变量**，通过将加密的png图片转换为.pvr.ccz文件再用TexturePacker转换回png。

2. `DecryptUF.py`：同上，但是集成了解密功能，不需要下载TP以及环境，输入两个参数输入目录和输出目录不指定就是直接替换原文件

   ```python
   python DecryptUF.py . .
   ```

3. `DecryptXOR.py`/`DecryptXORTest.py`： 功能一致，Test是前者的完全版，检测Bundle文件的异或加密种类，可以尝试更多种类的XOR加密，用于处理unity资源的XOR加密。

4. `Decrypt64B-XOR(GirlsLoveDance).py`：处理 千娇百媚 的文件前64个字节XOR加密

5. `WPKUnpacker.py`：解密WPK文件，通常会得到LPK、config、png；调用了本地bandizip进行解压，使用了bandizip6.29的bc.exe命令行工具，高级版本为bz.exe，需要把bc添加到环境变量

6. `LPKUnpacker.py`：解密LPK文件，需要配合config.json文件一起使用；支持Live2D和Spine 

7. `YooAssetUnpacker.py`：用于处理Unity的YooAsset资产框架解密。经典目录结构就是Package目录下有ManifestFiles和CacheBundleFiles，处理完之后就是正常的unity文件

8. 1

## ArkRecode

星陨计划下载脚本，无加密。

1. `CatalogCatcher.py`：执行后会自动下载最新的catalog清单。

2. `CatalogComparer.py`：比较两个新旧两个版本的catalog清单，获取更新条目，输出到当前目录下`catalog_107966-time.json`，time是时间戳。

   ```python
   python CatalogComparer.py catalog_107965.json catalog_107966.json
   ```

   

3. `UpdateDownloader.py`：输入更新清单自动下载输出到output目录下，下载失败的URL输出到404.log

   ```python
   python UpdateDownloader.py catalog_107966-time.json
   ```

4. 



## CherryTale

用下载器下载的资源会自动解密。

下载器是编译好的版本，来自[CherryTale_AssetDecDL](https://github.com/28598519a/CherryTale_AssetDecDL/tree/main)

PC端清单`index_save.txt`路径`.\AppData\LocalLow\SuperHGame\Cherry Tale\Patch`

移动端应该类似，可能在`/data/usr/0`里面

1. `CherryTaleDecrypt.py`：需要把资源放在input目录，然后创建一个空的output目录，只用于樱境物语解密资源

      ```python
      python CherryTaleDecrypt.py input output
      ```

2. `CatalogJsonDiff.py`：可以比较两个json文件的键差异并输出这些差异键以及对应的值。因为通常资源清单更新的文件是新的键，所以更新资源只需要下载这些更新的键即可，不需要再次下载完整的资源。对于樱境物语，只需要比较两个不同时间段的index_save.txt（实际为json格式），然后把结果输出到一个新的index.txt，你可以把2024.6.3得到的清单命名为2024.6.3.json，2025.12.1得到的命名为2025.12.1.json，然后用这个脚本运行，会自动输出一个`index.update-20251201_130906.txt`类似的文件，然后再用下载器下载这个文件清单记载的文件。

   ```python
   python CatalogJsonDiff.py 2024.6.3.json 2025.12.1.json
   ```

3. `CherryTaleDownloader.exe`：选择index.txt进行下载，下载失败的文件会输出到`404.log`日志里面

4. `TryDownLoadError.py`：默认读取`404.log`进行重新下载。注意这里下载的是未解密的源文件，需要再使用解密脚本处理。





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

7. `ExtractAllSubFiles.py`：提取当前目录以及子目录下的所有文件到_extracted_files目录下。

8. `ExtractSecondaryFiles.py`：当前目录下的所有纯文件目录会被往上提取（到父级目录）。

   注意脚本使用目录位置：

   ![image-20251202180654156](https://cdn.jsdelivr.net/gh/violet-wdream/Drawio/PNG/202512021806190.png)

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

   

9. `DelDirSuf(.unity3d_export)&MvCAB`：删除所有的目录特定后缀（.unity3d_export），可自定义，同时将下一级CAB目录的内容移到上一级。

10. `DelDirSuf(_res_export)&MvCAB`：同理。

11. `DelErrorEmptyDir(Drag File)`：有时候会莫名生成空的目录，然后删不掉，就把目录拖到这个bat上删除，注意：这个删除方式不会放到回收站。

12. `DelFileSuf(.asset)`：删除所有文件的后缀.asset

13. `DelFileSuf(.prefab)`：同理删除所有文件的后缀.prefab

14. 

