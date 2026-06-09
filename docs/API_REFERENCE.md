# DSSAT API 接口文档

## 1. 基本信息

服务地址：`http://127.0.0.1:8765`

服务入口：`services/dssat_api.py`

启动命令：

```powershell
python services\dssat_api.py
```

当前服务将 DSSAT-CSM 玉米模型封装为本地 HTTP API：接收种植情景参数，生成 DSSAT 输入文件，运行模型，并返回结构化产量结果。

## 2. 健康检查

### `GET /health`

请求：

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8765/health -Method GET
```

响应：

```json
{
  "status": "ok",
  "dssatRoot": "C:\\DSSAT48"
}
```

字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `status` | string | 服务状态 |
| `dssatRoot` | string | DSSAT 运行目录 |

## 3. 玉米产量模拟

### `POST /simulate/maize-yield`

请求头：`Content-Type: application/json`

请求体：

```json
{
  "location": { "name": "Harbin default", "lat": 45.75, "lon": 126.63, "elevationM": 150 },
  "crop": { "type": "maize", "model": "MZCER048", "cultivarCode": "990002" },
  "plantingDate": "2026-05-15",
  "management": {
    "plantDensityPlantsHa": 67500,
    "rowSpacingCm": 65,
    "rainfed": true,
    "fertilizer": { "nitrogenKgHa": 150, "phosphorusKgHa": 60, "potassiumKgHa": 60 }
  }
}
```

请求字段：

| 字段 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `location.name` | string | `Harbin default field` | 地点名称 |
| `location.lat` | number | `45.75` | 纬度 |
| `location.lon` | number | `126.63` | 经度 |
| `location.elevationM` | number | `150` | 海拔，米 |
| `crop.type` | string | `maize` | 当前仅支持玉米 |
| `crop.model` | string | `MZCER048` | DSSAT 玉米模型 |
| `crop.cultivarCode` | string | `990002` | DSSAT 品种代码；`990002` 为中熟玉米 |
| `plantingDate` | string | `2026-05-15` | 播种日期，格式 `YYYY-MM-DD` |
| `management.plantDensityPlantsHa` | number | `67500` | 种植密度，株/公顷 |
| `management.rowSpacingCm` | number | `65` | 行距，厘米 |
| `management.rainfed` | boolean | `true` | 当前最小版按雨养处理 |
| `management.fertilizer.nitrogenKgHa` | number | `150` | 施氮量，kg/ha |
| `management.fertilizer.phosphorusKgHa` | number | `60` | 施磷量，kg/ha |
| `management.fertilizer.potassiumKgHa` | number | `60` | 施钾量，kg/ha |

## 4. 响应体

成功响应：

```json
{
  "runId": "run_20260603_210440_12c7f69d",
  "status": "success",
  "returnCode": 0,
  "scenario": {},
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
    "runDir": "runs/run_xxx",
    "summary": "runs/run_xxx/Summary.OUT",
    "overview": "runs/run_xxx/OVERVIEW.OUT",
    "warning": "runs/run_xxx/WARNING.OUT"
  }
}
```

结果字段：

| 字段 | 说明 |
| --- | --- |
| `runId` | 本次调用唯一 ID |
| `status` | `success` 或 `error` |
| `returnCode` | DSSAT 退出码，`0` 为成功 |
| `scenario` | 原始请求参数 |
| `result.yieldKgHa` | 公顷产量，kg/ha |
| `result.yieldKgMu` | 亩产，kg/亩 |
| `result.anthesisDays` | 播种后多少天开花 |
| `result.maturityDays` | 播种后多少天成熟 |
| `result.biomassKgHa` | 地上部总生物量，kg/ha |
| `result.rainMm` | 生长期降雨量，mm |
| `result.irrigationMm` | 灌溉量，mm |
| `result.evapotranspirationMm` | 蒸散/耗水量，mm |
| `result.nitrogenUptakeKgHa` | 作物吸氮量，kg/ha |
| `files.*` | 原始 DSSAT 输出文件保存路径 |

## 5. PowerShell 调用示例

```powershell
$body = @{
  location = @{ name='Harbin default'; lat=45.75; lon=126.63; elevationM=150 }
  crop = @{ type='maize'; model='MZCER048'; cultivarCode='990002' }
  plantingDate = '2026-05-15'
  management = @{
    plantDensityPlantsHa = 67500
    rowSpacingCm = 65
    rainfed = $true
    fertilizer = @{ nitrogenKgHa=150; phosphorusKgHa=60; potassiumKgHa=60 }
  }
} | ConvertTo-Json -Depth 6

Invoke-RestMethod -Uri http://127.0.0.1:8765/simulate/maize-yield -Method POST -Body $body -ContentType 'application/json'
```

## 6. 错误响应

服务异常：

```json
{ "status": "error", "error": "错误信息" }
```

DSSAT 失败：

```json
{ "status": "error", "returnCode": 2, "stderr": "Fortran runtime error ..." }
```

## 7. 当前限制

```text
1. 当前只支持玉米默认情景。
2. 天气由服务生成，为默认合成天气，不是真实天气预报。
3. 土壤使用默认近似土壤，不是严格黑龙江本地黑土。
4. 服务内部使用锁避免并发覆盖，但暂未实现任务队列。
5. 输出文件会复制到 runs/run_xxx 目录，便于智能体读取。
```
