import hashlib

from django.core.cache import cache


def is_rate_limited(request, *, key_prefix, limit, window):
    """Return whether this client exceeded a fixed-window public request limit."""
    client_ip = request.META.get("REMOTE_ADDR", "unknown")
    key = "mealstack:ratelimit:{}:{}".format(
        key_prefix,
        hashlib.sha256(client_ip.encode("utf-8", errors="replace")).hexdigest(),
    )
    if cache.add(key, 1, timeout=window):
        return False
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=window)
        return False
    return count > limit
