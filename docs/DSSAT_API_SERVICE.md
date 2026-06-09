# DSSAT API 服务说明

本服务把 DSSAT-CSM 命令行模型封装为本地 HTTP API，供智能体或其他程序调用。

## 1. 服务文件

```text
services/dssat_api.py
```

默认依赖：

```text
Python 3.7+
C:\DSSAT48\DSCSM048.EXE
C:\DSSAT48\Maize
C:\DSSAT48\Weather
C:\DSSAT48\Soil
```

## 2. 启动服务

在项目根目录执行：

```powershell
python services\dssat_api.py
```

默认监听：

```text
http://127.0.0.1:8765
```

环境变量：

```text
DSSAT_ROOT  DSSAT 运行目录，默认 C:\DSSAT48
DSSAT_RUNS  每次调用输出保存目录，默认 ./runs
PORT        API 端口，默认 8765
```

## 3. 健康检查

```http
GET /health
```

返回示例：

```json
{
  "status": "ok",
  "dssatRoot": "C:\\DSSAT48"
}
```

## 4. 玉米产量模拟接口

```http
POST /simulate/maize-yield
```

### 请求 JSON Schema

```json
{
  "location": {
    "name": "Harbin default",
    "lat": 45.75,
    "lon": 126.63,
    "elevationM": 150
  },
  "crop": {
    "type": "maize",
    "model": "MZCER048",
    "cultivarCode": "990002"
  },
  "plantingDate": "2026-05-15",
  "management": {
    "plantDensityPlantsHa": 67500,
    "rowSpacingCm": 65,
    "rainfed": true,
    "fertilizer": {
      "nitrogenKgHa": 150,
      "phosphorusKgHa": 60,
      "potassiumKgHa": 60
    }
  }
}
```

### 字段说明

```text
location.lat/lon/elevationM   地点坐标和海拔
crop.cultivarCode             DSSAT 玉米品种参数，默认 990002 中熟品种
plantingDate                  播种日期，YYYY-MM-DD
plantDensityPlantsHa          种植密度，株/公顷
rowSpacingCm                  行距，厘米
rainfed                       是否雨养；当前最小版按雨养处理
fertilizer                    氮磷钾投入，kg/ha
```

## 5. 调用示例

PowerShell：

```powershell
$body = @{
  location = @{ name='Harbin default'; lat=45.75; lon=126.63; elevationM=150 }
  crop = @{ type='maize'; model='MZCER048'; cultivarCode='990002' }
  plantingDate = '2026-05-15'
  management = @{
    plantDensityPlantsHa=67500
    rowSpacingCm=65
    rainfed=$true
    fertilizer=@{ nitrogenKgHa=150; phosphorusKgHa=60; potassiumKgHa=60 }
  }
} | ConvertTo-Json -Depth 6

Invoke-RestMethod -Uri http://127.0.0.1:8765/simulate/maize-yield `
  -Method POST -Body $body -ContentType 'application/json'
```

## 6. 响应 JSON

成功响应示例：

```json
{
  "runId": "run_20260603_210440_12c7f69d",
  "status": "success",
  "returnCode": 0,
  "result": {
    "anthesisDays": 63,
    "maturityDays": 111,
    "biomassKgHa": 19394,
    "yieldKgHa": 8774,
    "yieldKgMu": 584.9,
    "rainMm": 416,
    "irrigationMm": 0,
    "evapotranspirationMm": 456,
    "soilWaterMm": 75,
    "nitrogenUptakeKgHa": 185
  },
  "files": {
    "runDir": "runs/...",
    "summary": "runs/.../Summary.OUT",
    "overview": "runs/.../OVERVIEW.OUT",
    "warning": "runs/.../WARNING.OUT"
  }
}
```

## 7. 当前限制

```text
1. 当前是最小可用版，只封装玉米产量默认情景。
2. 天气为服务生成的默认合成天气，不是真实天气预报。
3. 土壤使用默认近似土壤，不是严格黑龙江本地黑土。
4. DSSAT 主目录会被临时写入输入文件，服务内部用锁避免并发冲突。
5. 每次调用会把输出复制到独立 runs/run_xxx 目录。
```
