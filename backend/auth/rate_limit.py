import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None


class RedisRateLimiter:
    """Redis-backed limiter with in-memory fallback for local/test environments."""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._memory_windows: Dict[str, Deque[float]] = defaultdict(deque)
        self._redis = None
        if redis is not None:
            try:
                self._redis = redis.Redis.from_url(redis_url, decode_responses=True)
                self._redis.ping()
            except Exception:
                self._redis = None

    def _check_memory(self, key: str, limit: int, window_seconds: int) -> Tuple[bool, int]:
        now = time.time()
        bucket = self._memory_windows[key]
        while bucket and bucket[0] <= now - window_seconds:
            bucket.popleft()
        if len(bucket) >= limit:
            retry_after = int(window_seconds - (now - bucket[0])) if bucket else window_seconds
            return False, max(retry_after, 1)
        bucket.append(now)
        return True, 0

    def _check_redis(self, key: str, limit: int, window_seconds: int) -> Tuple[bool, int]:
        assert self._redis is not None
        now_ms = int(time.time() * 1000)
        window_start = now_ms - (window_seconds * 1000)
        pipe = self._redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(now_ms): now_ms})
        pipe.expire(key, window_seconds)
        _, count, _, _ = pipe.execute()
        if int(count) >= limit:
            return False, window_seconds
        return True, 0

    def check(self, key: str, limit: int, window_seconds: int) -> Tuple[bool, int]:
        if self._redis is not None:
            try:
                return self._check_redis(key, limit, window_seconds)
            except Exception:
                # Fail open to fallback memory limiter.
                pass
        return self._check_memory(key, limit, window_seconds)
