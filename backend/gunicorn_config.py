# gunicorn_config.py
# Gunicorn配置文件 - 用于生产环境部署

import os
import multiprocessing

# 服务器配置
bind = f"0.0.0.0:{os.getenv('PORT', '5001')}"
backlog = 2048

# Worker配置
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = "gevent"  # 使用gevent异步worker
worker_connections = 1000
max_requests = 1000  # 每个worker处理的最大请求数
max_requests_jitter = 100  # 随机抖动
preload_app = True  # 预加载应用

# 超时配置
timeout = 30
keepalive = 2
graceful_timeout = 30

# 日志配置
accesslog = "-"  # 输出到stdout
errorlog = "-"   # 输出到stderr
loglevel = os.getenv('LOG_LEVEL', 'info').lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 进程命名
proc_name = 'shenlun-backend'

# 安全配置
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# 性能优化
max_requests_jitter = 100
worker_tmp_dir = '/dev/shm'  # 使用内存文件系统

# 钩子函数
def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_worker_init(worker):
    worker.log.info("Worker initialized (pid: %s)", worker.pid)

def worker_abort(worker):
    worker.log.info("Worker aborted (pid: %s)", worker.pid)