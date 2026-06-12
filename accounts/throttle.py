"""
Simple cache-based rate limiting for auth endpoints.
No external dependencies — uses Django's cache framework.
"""

from functools import wraps

from django.core.cache import cache
from django.shortcuts import render


def _client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if xff:  # Railway/Heroku put the real client first
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


def rate_limit(key_prefix, max_attempts=8, window_seconds=300):
    """
    Limits POST requests per client IP. GET requests are never throttled.
    After max_attempts POSTs within the window, returns a friendly 429 page.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.method == 'POST':
                cache_key = f'rl:{key_prefix}:{_client_ip(request)}'
                attempts = cache.get(cache_key, 0)
                if attempts >= max_attempts:
                    return render(request, 'rate_limited.html', status=429)
                cache.set(cache_key, attempts + 1, window_seconds)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
