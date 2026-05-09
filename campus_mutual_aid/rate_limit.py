"""
登录和注册接口限流装饰器。
在 settings.py 中需要配置 CACHES 以启用。
"""
import time
from functools import wraps

from django.core.cache import cache
from django.http import HttpResponse
from django.conf import settings


def rate_limit(key_prefix, max_requests=5, period=60):
    """
    基于缓存的时间窗口限流装饰器。
    key_prefix: 缓存键前缀
    max_requests: 时间窗口内最大请求数
    period: 时间窗口（秒）
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if settings.DEBUG:
                return view_func(request, *args, **kwargs)

            client_ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
            cache_key = f'rate_limit:{key_prefix}:{client_ip}'
            timestamps = cache.get(cache_key, [])

            now = time.time()
            timestamps = [t for t in timestamps if now - t < period]
            timestamps.append(now)

            if len(timestamps) > max_requests:
                return HttpResponse('请求过于频繁，请稍后再试', status=429)

            cache.set(cache_key, timestamps, timeout=period)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
