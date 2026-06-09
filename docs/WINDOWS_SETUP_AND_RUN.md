# Windows 下配置、编译并运行 DSSAT-CSM

本文记录本仓库在 Windows 上从源码编译、配置完整数据目录并运行玉米样例的步骤。

## 1. 项目说明

DSSAT-CSM 是 Fortran 编写的作物/农田系统模拟模型。它不是网页项目，也不是常规 GUI 项目，而是命令行模型程序。

本次最终运行目录与程序：

```text
C:\DSSAT48
C:\DSSAT48\DSCSM048.EXE
```

## 2. 编译环境

Windows 下使用：Git for Windows、CMake、MSYS2、MSYS2 UCRT64 gfortran、ninja。

安装 Fortran 编译环境：

```powershell
C:\msys64\usr\bin\bash.exe -lc "pacman -Sy --noconfirm mingw-w64-ucrt-x86_64-gcc-fortran mingw-w64-ucrt-x86_64-cmake mingw-w64-ucrt-x86_64-ninja"
```

## 3. 编译源码

源码目录：

```text
C:\xiangmu\dssat-csm-os
```

配置与编译：

```powershell
C:\msys64\usr\bin\bash.exe -lc "cd /c/xiangmu/dssat-csm-os && export PATH=/ucrt64/bin:$PATH && cmake -S . -B build-msys -G Ninja -DCMAKE_Fortran_COMPILER=/ucrt64/bin/gfortran.exe -DCMAKE_BUILD_TYPE=Release"
C:\msys64\usr\bin\bash.exe -lc "cd /c/xiangmu/dssat-csm-os && export PATH=/ucrt64/bin:$PATH && cmake --build build-msys --parallel 4"
```

编译产物：

```text
C:\xiangmu\dssat-csm-os\build-msys\bin\dscsm048.exe
```

## 4. 下载完整数据

完整数据仓库：

```powershell
git clone --depth 1 https://github.com/DSSAT/dssat-csm-data.git C:\xiangmu\dssat-csm-data
```

## 5. 组装 C:\DSSAT48

执行：

```powershell
New-Item -ItemType Directory -Force C:\DSSAT48 | Out-Null
Copy-Item -Path C:\xiangmu\dssat-csm-os\Data\* -Destination C:\DSSAT48 -Recurse -Force
Copy-Item -Path C:\xiangmu\dssat-csm-data\* -Destination C:\DSSAT48 -Recurse -Force
Copy-Item -Path C:\xiangmu\dssat-csm-os\build-msys\bin\dscsm048.exe -Destination C:\DSSAT48\DSCSM048.EXE -Force
Copy-Item -Path C:\xiangmu\dssat-csm-os\Data\BatchFiles\Maize.v48 -Destination C:\DSSAT48\DSSBatch.v48 -Force
```

组装后关键文件/目录：

```text
C:\DSSAT48\DSCSM048.EXE
C:\DSSAT48\DSSBatch.v48
C:\DSSAT48\DSCSM048.CTR
C:\DSSAT48\MODEL.ERR
C:\DSSAT48\Genotype
C:\DSSAT48\Maize
C:\DSSAT48\Weather
C:\DSSAT48\Soil
```

## 6. 运行玉米样例

```powershell
cd C:\DSSAT48
.\DSCSM048.EXE MZCER048 B DSSBatch.v48 DSCSM048.CTR
```

本次验证已成功，返回码为 `0`，输出示例：

```text
RUN    TRT FLO MAT TOPWT HARWT  RAIN  TIRR   CET  PESW  TNUP  TNLF   TSON TSOC
  1 MZ   1  53 118 10788  4329   391     0   306     9   130    19  12349  169
```

## 7. 查看结果

输出文件位于 `C:\DSSAT48`。常用文件：

```text
Summary.OUT
OVERVIEW.OUT
Evaluate.OUT
PlantGro.OUT
Weather.OUT
MgmtOps.OUT
WARNING.OUT
INFO.OUT
```

查看结果：

```powershell
notepad C:\DSSAT48\Summary.OUT
notepad C:\DSSAT48\OVERVIEW.OUT
```

## 8. 通俗理解：输入是什么，输出是什么

这个程序可以理解为：给它一块田的种植方案和环境数据，它模拟作物怎么长，最后告诉你产量、水分、氮素等结果。

### 输入是什么

本次运行命令是：

```powershell
.\DSCSM048.EXE MZCER048 B DSSBatch.v48 DSCSM048.CTR
```

含义如下：

```text
DSCSM048.EXE   模型程序
MZCER048       玉米模型
B              批处理模式
DSSBatch.v48   要跑哪些试验/处理的任务清单
DSCSM048.CTR   模拟控制配置
```

真正的输入可以概括为：

```text
作物：玉米
品种：玉米品种参数
地点：试验地点、经纬度、海拔
土壤：土壤层次、水分、养分等参数
天气：每天温度、降雨、太阳辐射
管理：播种、施肥、灌溉、收获等操作
任务：批量跑哪些实验文件和第几个处理
```

例如 `DSSBatch.v48` 像一张任务清单，告诉模型去跑：

```text
C:\DSSAT48\Maize\BRPI0202.MZX 的第 1 个处理
C:\DSSAT48\Maize\BRPI0202.MZX 的第 2 个处理
C:\DSSAT48\Maize\UFGA8201.MZX 的第 1 个处理
```

每个 `.MZX` 文件就是一个玉米试验方案，里面描述什么时候种、种什么品种、土壤是什么、天气用哪个文件、施多少肥、灌不灌水等。

### 输出是什么

模型运行后会在 `C:\DSSAT48` 生成很多 `.OUT` 文件。通俗讲：

```text
Summary.OUT    最终成绩单：产量、成熟时间、耗水、吸氮等汇总结果
OVERVIEW.OUT   过程说明书：这次模拟用了哪些输入，关键阶段和最终结果
PlantGro.OUT   成长日记：每天叶面积、株高、生物量、籽粒重等变化
Weather.OUT    天气记录：模型实际读取/使用的天气过程
SoilWat.OUT    土壤水分：土壤含水量、蒸散、排水等
WARNING.OUT    警告记录：缺失参数、异常天气值等提示
```

`Summary.OUT` 里的典型字段可以这样读：

```text
FLO     播种后多少天开花
MAT     播种后多少天成熟
TOPWT   地上部总生物量，kg/ha
HARWT   收获产量，kg/ha
RAIN    生长期降雨量，mm
TIRR    灌溉量，mm
CET     作物耗水/蒸散量，mm
TNUP    作物吸收氮量，kg/ha
```

例如一行结果：

```text
1 MZ 1 53 118 10788 4329 391 0 306
```

可以理解为：第 1 次模拟，玉米第 1 个处理，播种后 53 天开花、118 天成熟，最终产量约 4329 kg/ha，生长期降雨 391 mm，没有灌溉，作物耗水约 306 mm。

一句话总结：输入是“这块田怎么种、天气和土壤怎么样”，输出是“作物怎么长、什么时候成熟、最终产量多少、水和氮用了多少”。

## 9. 常见问题

### 9.1 `dscsm048.exe I` 报 `EXP.LST`

交互模式 `I` 依赖 DSSAT 交互实验列表 `EXP.LST`。当前建议用批处理模式 `B` 跑样例：

```powershell
cd C:\DSSAT48
.\DSCSM048.EXE MZCER048 B DSSBatch.v48 DSCSM048.CTR
```

### 9.2 PowerShell 界面乱码

老式 Fortran 控制台界面可能乱码。可先执行 `chcp 437`，但批处理模式通常不需要交互界面。

### 9.3 `WARNING.OUT` 有警告

样例可能出现土壤参数缺省、辐射值偏低等警告。这些来自示例数据，不影响本次样例跑通。

## 10. 日常运行

```powershell
cd C:\DSSAT48
.\DSCSM048.EXE MZCER048 B DSSBatch.v48 DSCSM048.CTR
notepad Summary.OUT
```
