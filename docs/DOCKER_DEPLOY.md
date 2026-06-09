# DSSAT API Docker 部署说明

本文说明如何把 DSSAT 作物模拟 API 部署到 Linux 服务器。

服务启动后默认端口：

```text
8765
```

主要接口：

```text
GET  /health
GET  /crops
GET  /locations
POST /simulate/crop-yield
```

---

## 1. 前置条件

服务器建议：

```text
系统：Ubuntu 20.04+/Debian 11+/CentOS 8+
内存：建议 4GB+
磁盘：建议 10GB+
网络：构建镜像时需要访问 GitHub
```

需要安装：

```bash
docker --version
docker compose version
```

如果服务器未安装 Docker，可参考：

```bash
curl -fsSL https://get.docker.com | bash
sudo systemctl enable docker
sudo systemctl start docker
```

---

## 2. 拉取项目代码

```bash
git clone https://github.com/chenggong0306/dssat.git
cd dssat
```

如果已经拉过代码：

```bash
git pull
```

---

## 3. 构建 Docker 镜像

```bash
docker build -t dssat-api:latest .
```

构建过程会自动完成：

```text
1. 安装 gfortran/cmake/ninja 等编译工具
2. 编译 DSSAT Fortran 模型
3. 生成 Linux 可执行文件 /opt/dssat/dscsm048
4. 下载官方 DSSAT 数据仓库 dssat-csm-data
5. 组装 /opt/dssat 运行目录
6. 复制 Python API 服务
```

> 注意：构建时需要访问 `https://github.com/DSSAT/dssat-csm-data.git`。如果服务器无法访问 GitHub，需要改成离线数据 COPY 方案。

---

## 4. 使用 Docker Compose 启动

推荐使用 compose：

```bash
docker compose up -d --build
```

查看容器状态：

```bash
docker compose ps
```

查看日志：

```bash
docker compose logs -f dssat-api
```

停止服务：

```bash
docker compose down
```

---

## 5. 使用 docker run 启动

如果不用 compose，也可以直接运行：

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

---

## 6. 健康检查

本机测试：

```bash
curl http://127.0.0.1:8765/health
```

服务器外部访问：

```bash
curl http://服务器IP:8765/health
```

成功返回：

```json
{
  "status": "ok",
  "dssatRoot": "/opt/dssat"
}
```

---

## 7. 查看作物和地点

查看支持作物：

```bash
curl http://127.0.0.1:8765/crops
```

查看内置中国地点预设：

```bash
curl http://127.0.0.1:8765/locations
```

---

## 8. 调用模拟接口

使用经纬度调用，推荐生产系统采用这种方式：

```bash
curl -X POST http://127.0.0.1:8765/simulate/crop-yield \
  -H "Content-Type: application/json" \
  -d '{
    "crop": { "type": "maize" },
    "location": { "lat": 34.75, "lon": 113.62, "elevationM": 110, "code": "ZZCN" },
    "plantingDate": "2026-05-15"
  }'
```

使用城市预设调用：

```bash
curl -X POST http://127.0.0.1:8765/simulate/crop-yield \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{
    "crop": { "type": "rice" },
    "location": { "city": "武汉" },
    "plantingDate": "2026-05-20"
  }'
```

---

## 9. 环境变量

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `DSSAT_ROOT` | `/opt/dssat` | DSSAT 运行数据目录 |
| `DSSAT_EXE` | `/opt/dssat/dscsm048` | DSSAT Linux 可执行文件 |
| `DSSAT_RUNS` | `/app/runs` | 每次模拟输出归档目录 |
| `HOST` | `0.0.0.0` | 容器内监听地址 |
| `PORT` | `8765` | 服务端口 |

---

## 10. 更新服务

拉取最新代码并重建：

```bash
git pull
docker compose up -d --build
```

清理旧镜像：

```bash
docker image prune -f
```

---

## 11. 常见问题

### 11.1 构建时 GitHub 下载失败

现象：

```text
git clone https://github.com/DSSAT/dssat-csm-data.git failed
```

原因：服务器无法访问 GitHub。

解决：先在能访问 GitHub 的机器下载数据，或配置代理；也可以后续把 Dockerfile 改成 COPY 本地数据目录。

### 11.2 端口无法访问

检查容器是否运行：

```bash
docker compose ps
```

检查服务器防火墙/安全组是否放行：

```text
TCP 8765
```

### 11.3 API 返回 error 或 STOP 99

查看运行输出：

```bash
docker compose logs -f dssat-api
```

也可以查看 `runs` 卷里的 `WARNING.OUT`，里面会记录 DSSAT 模型错误原因。

---

## 12. 生产部署建议

1. 不建议直接公网裸露 `8765`，建议放到 Nginx/API Gateway 后面。
2. 建议加 API Key、JWT 或内网访问控制。
3. 当前 DSSAT 运行目录共享固定输出文件，服务内部用锁串行执行模拟；高并发场景建议改为每次请求复制独立工作目录。
4. 当前天气为合成天气，生产估产应接入真实逐日天气、土壤和品种参数。
5. `dssat-runs` 卷会持续保存输出文件，建议配置定期清理策略。
