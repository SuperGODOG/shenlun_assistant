# 申论助手后端部署指南

## 概述

本文档介绍如何部署申论助手后端服务，包括开发环境、生产环境以及负载均衡配置。

## 新增功能

### 并发控制和性能优化

- ✅ **请求限流**: 每分钟最多60个请求（可配置）
- ✅ **并发控制**: 最多10个并发请求（可配置）
- ✅ **响应缓存**: 智能缓存LLM响应，提高性能
- ✅ **性能监控**: 实时监控请求数量、响应时间、缓存命中率
- ✅ **健康检查**: 服务健康状态监控
- ✅ **负载均衡准备**: 支持多实例部署

## 快速开始

### 1. 开发环境

```bash
# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
./start.sh dev
```

### 2. 生产环境

```bash
# 使用Gunicorn启动
./start.sh prod

# 或者直接使用gunicorn
gunicorn --config gunicorn_config.py app:app
```

### 3. Docker部署

```bash
# 构建镜像
docker build -t shenlun-backend .

# 运行容器
docker run -p 5001:5001 shenlun-backend

# 使用docker-compose
docker-compose up -d
```

## 环境变量配置

### 基础配置

```bash
# 服务配置
PORT=5001
FLASK_ENV=production
LOG_LEVEL=INFO

# 并发控制
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=30
RATE_LIMIT_PER_MINUTE=60

# 缓存配置
ENABLE_RESPONSE_CACHE=true
CACHE_TTL_SECONDS=300
MAX_CACHE_SIZE=100

# 健康检查
HEALTH_CHECK_ENABLED=true
SERVER_ID=server-1

# 性能监控
ENABLE_METRICS=true
METRICS_COLLECTION_INTERVAL=60
```

### Gunicorn配置

```bash
# Worker配置
GUNICORN_WORKERS=4  # 建议: CPU核心数 * 2 + 1
WORKER_CLASS=gevent
WORKER_CONNECTIONS=1000

# 数据库连接池(未来扩展)
DB_POOL_SIZE=5
DB_POOL_TIMEOUT=30
```

## API端点

### 核心功能

- `POST /api/chat` - 聊天接口（带并发控制）
- `GET /api/knowledge/search` - 知识库搜索
- `POST /api/knowledge/add` - 添加知识库文档

### 监控和管理

- `GET /health` - 健康检查
- `GET /api/metrics` - 性能指标
- `POST /api/cache/clear` - 清空缓存

### 性能指标示例

```json
{
  "total_requests": 150,
  "concurrent_requests": 2,
  "cache_hit_rate": 0.75,
  "rate_limited_requests": 5,
  "average_response_time": 1.234,
  "cache_size": 45
}
```

## 负载均衡配置

### 使用Nginx

1. **启动多个后端实例**:

```bash
# 实例1
PORT=5001 SERVER_ID=server-1 ./start.sh prod

# 实例2
PORT=5002 SERVER_ID=server-2 ./start.sh prod

# 实例3
PORT=5003 SERVER_ID=server-3 ./start.sh prod
```

2. **配置Nginx**:

```nginx
upstream shenlun_backend {
    least_conn;
    server localhost:5001 max_fails=3 fail_timeout=30s;
    server localhost:5002 max_fails=3 fail_timeout=30s;
    server localhost:5003 max_fails=3 fail_timeout=30s;
}
```

3. **启动Nginx**:

```bash
# 使用提供的配置文件
nginx -c /path/to/nginx.conf

# 或使用docker-compose
docker-compose --profile load-balancer up -d
```

### 使用Docker Swarm

```bash
# 初始化swarm
docker swarm init

# 部署服务
docker service create \
  --name shenlun-backend \
  --replicas 3 \
  --publish 5001:5001 \
  shenlun-backend
```

## 监控和日志

### 日志配置

```python
# 日志级别: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO
LOG_FORMAT='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
```

### 性能监控

```bash
# 查看实时指标
curl http://localhost:5001/api/metrics

# 健康检查
curl http://localhost:5001/health

# 清空缓存
curl -X POST http://localhost:5001/api/cache/clear
```

## 故障排除

### 常见问题

1. **服务器繁忙 (503错误)**
   - 检查并发请求数是否超过限制
   - 增加 `MAX_CONCURRENT_REQUESTS` 值
   - 添加更多worker进程

2. **请求过于频繁 (429错误)**
   - 检查客户端请求频率
   - 调整 `RATE_LIMIT_PER_MINUTE` 值
   - 实施客户端请求缓存

3. **响应时间过长**
   - 检查LLM API响应时间
   - 启用响应缓存
   - 优化知识库查询

### 性能调优建议

1. **并发设置**:
   - 开发环境: `MAX_CONCURRENT_REQUESTS=5`
   - 生产环境: `MAX_CONCURRENT_REQUESTS=20-50`

2. **缓存策略**:
   - 启用响应缓存: `ENABLE_RESPONSE_CACHE=true`
   - 合理设置TTL: `CACHE_TTL_SECONDS=300-600`

3. **Worker配置**:
   - CPU密集型: `workers = CPU核心数 + 1`
   - IO密集型: `workers = CPU核心数 * 2 + 1`

## 安全考虑

1. **API访问控制**
   - 实施API密钥认证
   - 配置CORS策略
   - 使用HTTPS

2. **资源限制**
   - 设置合理的请求大小限制
   - 配置超时时间
   - 监控资源使用情况

3. **日志安全**
   - 避免记录敏感信息
   - 定期轮转日志文件
   - 设置适当的日志级别

## 扩展计划

### 短期优化
- [ ] 数据库连接池
- [ ] Redis缓存集成
- [ ] API认证系统

### 长期规划
- [ ] 微服务架构
- [ ] 消息队列集成
- [ ] 分布式缓存
- [ ] 自动扩缩容

## 联系支持

如有问题，请查看日志文件或联系技术支持团队。