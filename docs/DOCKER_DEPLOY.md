# DSSAT API Docker 部署说明

本文说明如何把 DSSAT API 服务部署到 Linux 服务器。

## 1. 构建镜像

在项目根目录执行：

```bash
docker build -t dssat-api:latest .
```

构建过程会：

1. 安装 gfortran/cmake/ninja；
2. 编译 DSSAT-CSM，生成 `/opt/dssat/dscsm048`；
3. 拉取官方数据仓库 `dssat-csm-data`；
4. 组装 `/opt/dssat` 运行目录；
5. 复制 Python API 服务。

> 注意：构建时需要服务器能访问 GitHub，用来下载 `dssat-csm-data`。

## 2. 运行容器

```bash
docker run -d \
  --name dssat-api \
  -p 8765:8765 \
  -e DSSAT_ROOT=/opt/dssat \
  -e DSSAT_EXE=/opt/dssat/dscsm048 \
  -e DSSAT_RUNS=/app/runs \
  -e HOST=0.0.0.0 \
  -e PORT=8765 \
  -v dssat-runs:/app/runs \
  dssat-api:latest
```

或者用 compose：

```bash
docker compose up -d --build
```

## 3. 健康检查

```bash
curl http://127.0.0.1:8765/health
```

成功返回：

```json
{
  "status": "ok",
  "dssatRoot": "/opt/dssat"
}
```

## 4. 查看支持作物

```bash
curl http://127.0.0.1:8765/crops
```

## 5. 查看地点预设

```bash
curl http://127.0.0.1:8765/locations
```

## 6. 调用模拟接口

```bash
curl -X POST http://127.0.0.1:8765/simulate/crop-yield \
  -H "Content-Type: application/json" \
  -d '{
    "crop": { "type": "maize" },
    "location": { "lat": 34.75, "lon": 113.62, "elevationM": 110, "code": "ZZCN" },
    "plantingDate": "2026-05-15"
  }'
```

也可以使用城市预设：

```bash
curl -X POST http://127.0.0.1:8765/simulate/crop-yield \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{
    "crop": { "type": "rice" },
    "location": { "city": "武汉" },
    "plantingDate": "2026-05-20"
  }'
```

## 7. 环境变量

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `DSSAT_ROOT` | `/opt/dssat` | DSSAT 运行数据目录 |
| `DSSAT_EXE` | `/opt/dssat/dscsm048` | DSSAT Linux 可执行文件 |
| `DSSAT_RUNS` | `/app/runs` | 每次模拟输出归档目录 |
| `HOST` | `0.0.0.0` | 容器内监听地址 |
| `PORT` | `8765` | 服务端口 |

## 8. 生产部署建议

1. 不要直接公网裸露服务，建议放在 Nginx/API Gateway 后面。
2. 加鉴权，例如 API Key、JWT 或内网访问控制。
3. 当前 DSSAT 运行目录共享固定输出文件，服务内部用锁串行执行模拟；高并发场景建议改为每次请求复制独立工作目录。
4. 当前天气为合成天气，生产估产应接入真实逐日天气、土壤和品种参数。
5. `dssat-runs` 卷会持续保存输出文件，需配置清理策略。
