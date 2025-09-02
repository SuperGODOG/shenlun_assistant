# middleware.py
# 中间件：并发控制、限流、缓存和性能监控

import time
import hashlib
import logging
from functools import wraps
from collections import defaultdict, OrderedDict
from threading import Lock
from flask import request, jsonify, g
from performance_config import (
    request_semaphore, 
    RATE_LIMIT_PER_MINUTE, 
    REQUEST_TIMEOUT,
    ENABLE_RESPONSE_CACHE,
    CACHE_TTL_SECONDS,
    MAX_CACHE_SIZE,
    ENABLE_METRICS
)

# 全局变量
rate_limit_storage = defaultdict(list)  # IP -> [timestamp, ...]
response_cache = OrderedDict()  # 响应缓存
cache_lock = Lock()  # 缓存锁
metrics_data = {
    'total_requests': 0,
    'concurrent_requests': 0,
    'cache_hits': 0,
    'cache_misses': 0,
    'rate_limited_requests': 0,
    'average_response_time': 0,
    'response_times': []
}
metrics_lock = Lock()

logger = logging.getLogger(__name__)

def get_client_ip():
    """获取客户端IP地址"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr

def rate_limit_check(ip):
    """检查IP是否超过速率限制"""
    current_time = time.time()
    minute_ago = current_time - 60
    
    # 清理过期的请求记录
    rate_limit_storage[ip] = [t for t in rate_limit_storage[ip] if t > minute_ago]
    
    # 检查是否超过限制
    if len(rate_limit_storage[ip]) >= RATE_LIMIT_PER_MINUTE:
        return False
    
    # 记录当前请求
    rate_limit_storage[ip].append(current_time)
    return True

def generate_cache_key(endpoint, args):
    """生成缓存键"""
    cache_string = f"{endpoint}:{str(sorted(args.items()))}"
    return hashlib.md5(cache_string.encode()).hexdigest()

def get_from_cache(cache_key):
    """从缓存获取响应"""
    if not ENABLE_RESPONSE_CACHE:
        return None
        
    with cache_lock:
        if cache_key in response_cache:
            cached_data, timestamp = response_cache[cache_key]
            if time.time() - timestamp < CACHE_TTL_SECONDS:
                # 移动到末尾(LRU)
                response_cache.move_to_end(cache_key)
                return cached_data
            else:
                # 过期，删除
                del response_cache[cache_key]
    return None

def set_cache(cache_key, data):
    """设置缓存"""
    if not ENABLE_RESPONSE_CACHE:
        return
        
    with cache_lock:
        # 如果缓存已满，删除最旧的条目
        if len(response_cache) >= MAX_CACHE_SIZE:
            response_cache.popitem(last=False)
        
        response_cache[cache_key] = (data, time.time())

def update_metrics(response_time, cache_hit=False, rate_limited=False):
    """更新性能指标"""
    if not ENABLE_METRICS:
        return
        
    with metrics_lock:
        metrics_data['total_requests'] += 1
        
        if cache_hit:
            metrics_data['cache_hits'] += 1
        else:
            metrics_data['cache_misses'] += 1
            
        if rate_limited:
            metrics_data['rate_limited_requests'] += 1
            
        # 更新响应时间
        metrics_data['response_times'].append(response_time)
        # 只保留最近1000个响应时间
        if len(metrics_data['response_times']) > 1000:
            metrics_data['response_times'] = metrics_data['response_times'][-1000:]
        
        # 计算平均响应时间
        if metrics_data['response_times']:
            metrics_data['average_response_time'] = sum(metrics_data['response_times']) / len(metrics_data['response_times'])

def concurrency_control(f):
    """并发控制装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        client_ip = get_client_ip()
        
        # 速率限制检查
        if not rate_limit_check(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            update_metrics(time.time() - start_time, rate_limited=True)
            return jsonify({
                'error': '请求过于频繁，请稍后再试',
                'code': 'RATE_LIMIT_EXCEEDED'
            }), 429
        
        # 尝试获取信号量(并发控制)
        if not request_semaphore.acquire(blocking=False):
            logger.warning(f"Max concurrent requests reached, rejecting request from IP: {client_ip}")
            return jsonify({
                'error': '服务器繁忙，请稍后再试',
                'code': 'SERVER_BUSY'
            }), 503
        
        try:
            with metrics_lock:
                metrics_data['concurrent_requests'] += 1
            
            # 检查缓存
            cache_key = None
            if ENABLE_RESPONSE_CACHE and request.method == 'POST':
                # 对于POST请求，基于请求数据生成缓存键
                request_data = request.get_json() or {}
                cache_key = generate_cache_key(request.endpoint, request_data)
                cached_response = get_from_cache(cache_key)
                
                if cached_response:
                    logger.info(f"Cache hit for key: {cache_key}")
                    response_time = time.time() - start_time
                    update_metrics(response_time, cache_hit=True)
                    return cached_response
            
            # 执行原函数
            g.start_time = start_time  # 存储开始时间供后续使用
            result = f(*args, **kwargs)
            
            # 缓存响应(仅对成功的响应)
            if cache_key and isinstance(result, tuple) and result[1] == 200:
                set_cache(cache_key, result)
            elif cache_key and not isinstance(result, tuple):
                # 默认200响应
                set_cache(cache_key, result)
            
            response_time = time.time() - start_time
            update_metrics(response_time, cache_hit=False)
            
            logger.info(f"Request processed in {response_time:.3f}s for IP: {client_ip}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing request from IP {client_ip}: {str(e)}")
            response_time = time.time() - start_time
            update_metrics(response_time)
            raise
        finally:
            with metrics_lock:
                metrics_data['concurrent_requests'] -= 1
            request_semaphore.release()
    
    return decorated_function

def get_metrics():
    """获取性能指标"""
    with metrics_lock:
        return {
            'total_requests': metrics_data['total_requests'],
            'concurrent_requests': metrics_data['concurrent_requests'],
            'cache_hit_rate': (
                metrics_data['cache_hits'] / 
                (metrics_data['cache_hits'] + metrics_data['cache_misses'])
                if (metrics_data['cache_hits'] + metrics_data['cache_misses']) > 0 else 0
            ),
            'rate_limited_requests': metrics_data['rate_limited_requests'],
            'average_response_time': round(metrics_data['average_response_time'], 3),
            'cache_size': len(response_cache)
        }

def clear_cache():
    """清空缓存"""
    with cache_lock:
        response_cache.clear()
    logger.info("Response cache cleared")