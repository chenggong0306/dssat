# 玉米产量模拟 API 接口文档

## 1. 接口说明

本 API 用于模拟指定作物在指定地点、播种日期和管理条件下的产量表现。当前服务已提供统一作物接口，玉米已可用，大豆、水稻、小麦、马铃薯已放入作物注册表，处于待实现状态。调用方提交种植情景参数，服务调用 DSSAT 作物模型，并返回产量、亩产、开花时间、成熟时间、生物量、降雨量、耗水量和吸氮量等结构化结果。

> 当前版本为默认情景模拟服务：天气为模型生成的默认合成天气，不等同于真实天气预报。

## 2. 服务地址

请将 `{BASE_URL}` 替换为实际部署地址，例如：

```text
https://api.example.com
```

## 3. 健康检查

```http
GET /health
```

示例：

```bash
curl {BASE_URL}/health
```

响应：

```json
{
  "status": "ok",
  "dssatRoot": "C:\\DSSAT48"
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `status` | string | 服务状态，正常为 `ok` |
| `dssatRoot` | string | 模型运行目录，调用方通常无需关心 |

## 4. 作物列表

```http
GET /crops
```

响应示例：

```json
{
  "crops": {
    "maize": { "model": "MZCER048", "yieldProduct": "grain", "status": "supported" },
    "rice": { "model": "RICER048", "yieldProduct": "grain", "status": "supported" },
    "wheat": { "model": "WHAPS048", "yieldProduct": "grain", "status": "supported" },
    "potato": { "model": "PTSUB048", "yieldProduct": "tuber", "status": "supported" },
    "barley": { "model": "CSCER048", "yieldProduct": "grain", "status": "supported" },
    "sorghum": { "model": "SGCER048", "yieldProduct": "grain", "status": "supported" },
    "sweetcorn": { "model": "SWCER048", "yieldProduct": "ear", "status": "supported" },
    "pearlmillet": { "model": "MLCER048", "yieldProduct": "grain", "status": "supported" },
    "sugarbeet": { "model": "BSCER048", "yieldProduct": "root", "status": "supported" },
    "soybean": { "model": "CRGRO048", "yieldProduct": "grain", "status": "planned" }
  }
}
```

`status=supported` 表示当前可调用；`status=planned` 表示已规划，但暂未开放模拟。

## 5. 地点预设列表

```http
GET /locations
```

返回内置中国城市/区域预设。调用方也可以不使用预设，直接在请求里传 `lat/lon/elevationM`。

示例响应节选：

```json
{
  "locations": {
    "郑州": { "province": "河南", "lat": 34.75, "lon": 113.62, "elevationM": 110 },
    "武汉": { "province": "湖北", "lat": 30.59, "lon": 114.31, "elevationM": 23 },
    "广州": { "province": "广东", "lat": 23.13, "lon": 113.26, "elevationM": 21 }
  }
}
```

## 6. 作物产量模拟

```http
POST /simulate/crop-yield
Content-Type: application/json
```

请求体：

```json
{
  "location": { "city": "郑州" },
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

## 5. 请求参数

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `location.city` | string | 可选 | 内置城市预设名，如 `郑州`、`武汉`、`广州`；可通过 `GET /locations` 查看 |
| `location.name` | string | `Custom location` | 地点名称；直接传经纬度时使用 |
| `location.lat` | number | `45.75` | 纬度；不使用城市预设时建议填写 |
| `location.lon` | number | `126.63` | 经度；不使用城市预设时建议填写 |
| `location.elevationM` | number | `150` | 海拔，米；不使用城市预设时建议填写 |
| `location.code` | string | 自动生成 | 4 位 ASCII 天气站代码；直接传经纬度时可自定义，如 `ZZCN` |
| `crop.type` | string | `maize` | 作物类型；当前支持 `maize`、`rice`、`wheat`、`potato`、`barley`、`sorghum`、`sweetcorn`、`pearlmillet`、`sugarbeet`；`soybean` 暂为 planned |
| `crop.model` | string | 自动选择 | DSSAT 模型代码；通常不需要调用方填写 |
| `crop.cultivarCode` | string | 作物默认品种 | DSSAT 品种代码；不填则使用各作物默认品种 |
| `plantingDate` | string | `2026-05-15` | 播种日期，格式 `YYYY-MM-DD` |
| `management.plantDensityPlantsHa` | number | `67500` | 种植密度，株/公顷 |
| `management.rowSpacingCm` | number | `65` | 行距，厘米 |
| `management.rainfed` | boolean | `true` | 是否雨养；当前版本按雨养情景处理 |
| `management.fertilizer.nitrogenKgHa` | number | `150` | 氮肥用量，kg/ha |
| `management.fertilizer.phosphorusKgHa` | number | `60` | 磷肥用量，kg/ha |
| `management.fertilizer.potassiumKgHa` | number | `60` | 钾肥用量，kg/ha |

## 6. 响应示例

```json
{
  "runId": "run_20260603_210440_12c7f69d",
  "status": "success",
  "returnCode": 0,
  "result": {
    "run": 1,
    "treatment": 1,
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
  }
}
```

## 7. 响应字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `runId` | string | 本次模拟任务 ID |
| `status` | string | `success` 表示成功，`error` 表示失败 |
| `returnCode` | number | 模型退出码，`0` 表示成功 |
| `result.anthesisDays` | number | 播种后多少天开花 |
| `result.maturityDays` | number | 播种后多少天成熟 |
| `result.biomassKgHa` | number | 地上部总生物量，kg/ha |
| `result.yieldKgHa` | number | 公顷产量，kg/ha |
| `result.yieldKgMu` | number | 亩产，kg/亩 |
| `result.rainMm` | number | 生长期降雨量，mm |
| `result.irrigationMm` | number | 灌溉量，mm |
| `result.evapotranspirationMm` | number | 作物耗水/蒸散量，mm |
| `result.soilWaterMm` | number | 模拟结束时土壤有效水，mm |
| `result.nitrogenUptakeKgHa` | number | 作物吸氮量，kg/ha |

## 8. 调用示例

curl：

```bash
curl -X POST "{BASE_URL}/simulate/crop-yield" \
  -H "Content-Type: application/json" \
  -d '{"crop":{"type":"maize"},"plantingDate":"2026-05-15"}'
```

JavaScript：

```js
const res = await fetch(`${BASE_URL}/simulate/crop-yield`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ crop: { type: "maize" }, plantingDate: "2026-05-15" })
});
const data = await res.json();
console.log(data.result.yieldKgMu);
```

## 9. 错误响应

服务异常：

```json
{ "status": "error", "error": "错误信息" }
```

模型运行失败：

```json
{ "status": "error", "returnCode": 2, "stderr": "Fortran runtime error ..." }
```

## 10. 使用注意事项

```text
1. 当前接口已支持玉米、水稻、小麦、马铃薯、大麦、高粱、甜玉米、珍珠粟、甜菜默认情景模拟；大豆已登记但当前仍为 planned。
2. 高粱、珍珠粟在当前哈尔滨默认情景下可能返回 `yieldKgHa=0`，表示该默认播期/品种/热量组合未形成可收获产量，不代表模型调用失败。
3. 当前土壤为默认近似土壤，不代表精确地块土壤。
4. 返回结果适合方案比较、模型演示和初步估产，不建议作为农业生产决策唯一依据。
5. 如需真实预测，应接入真实逐日天气、本地土壤和具体品种参数。
```
