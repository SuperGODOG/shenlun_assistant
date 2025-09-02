# performance_config.py
# 性能和并发控制配置

import os
from threading import Semaphore

# 并发控制配置
MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT_REQUESTS', '60'))  # 最大并发请求数
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '35'))  # 请求超时时间(秒)
RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', '60'))  # 每分钟最大请求数

# 创建信号量来控制并发
request_semaphore = Semaphore(MAX_CONCURRENT_REQUESTS)

# 缓存配置
ENABLE_RESPONSE_CACHE = os.getenv('ENABLE_RESPONSE_CACHE', 'true').lower() == 'true'
CACHE_TTL_SECONDS = int(os.getenv('CACHE_TTL_SECONDS', '600'))  # 缓存过期时间(秒)
MAX_CACHE_SIZE = int(os.getenv('MAX_CACHE_SIZE', '100'))  # 最大缓存条目数

# 健康检查配置
HEALTH_CHECK_ENABLED = os.getenv('HEALTH_CHECK_ENABLED', 'true').lower() == 'true'

# 日志配置
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# 性能监控配置
ENABLE_METRICS = os.getenv('ENABLE_METRICS', 'true').lower() == 'true'
METRICS_COLLECTION_INTERVAL = int(os.getenv('METRICS_COLLECTION_INTERVAL', '60'))  # 秒

# 数据库连接池配置(为未来扩展准备)
DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '5'))
DB_POOL_TIMEOUT = int(os.getenv('DB_POOL_TIMEOUT', '30'))

# 负载均衡准备配置
SERVER_ID = os.getenv('SERVER_ID', 'server-1')  # 服务器标识
HEALTH_CHECK_PORT = int(os.getenv('HEALTH_CHECK_PORT', '5002'))  # 健康检查端口