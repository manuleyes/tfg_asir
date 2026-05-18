"""
Backend Cache & Rate Limiting Configuration
"""
import redis
from slowapi import Limiter
from slowapi.util import get_remote_address
import json
import logging

logger = logging.getLogger(__name__)

# ============ REDIS CACHE ============
class RedisCache:
    """Simple Redis wrapper for caching"""
    
    _instance = None
    _redis_client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisCache, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        try:
            self._redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True
            )
            # Test connection
            self._redis_client.ping()
            logger.info(" Redis connected successfully")
        except redis.ConnectionError as e:
            logger.warning(f"️ Redis connection failed: {e}. Caching disabled.")
            self._redis_client = None
    
    def get(self, key: str):
        """Get value from cache"""
        if not self._redis_client:
            return None
        try:
            value = self._redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache GET error: {e}")
            return None
    
    def set(self, key: str, value, ttl: int = 300):
        """Set value in cache with TTL (seconds)"""
        if not self._redis_client:
            return False
        try:
            self._redis_client.setex(
                key,
                ttl,
                json.dumps(value, default=str)
            )
            return True
        except Exception as e:
            logger.error(f"Cache SET error: {e}")
            return False
    
    def delete(self, key: str):
        """Delete key from cache"""
        if not self._redis_client:
            return False
        try:
            self._redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache DELETE error: {e}")
            return False
    
    def flush_all(self):
        """Clear all cache"""
        if not self._redis_client:
            return False
        try:
            self._redis_client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Cache FLUSH error: {e}")
            return False
    
    def is_available(self):
        """Check if Redis is available"""
        return self._redis_client is not None


# ============ RATE LIMITING ============
limiter = Limiter(key_func=get_remote_address)

# Presets
RATE_LIMITS = {
    "default": "100/minute",      # 100 requests per minute
    "auth": "10/minute",          # Auth endpoints: 10 per minute
    "detection": "50/minute",     # Detection: 50 per minute
    "export": "20/minute",        # Export: 20 per minute
    "strict": "5/minute",         # Strict: 5 per minute
}

# Get redis instance
redis_cache = RedisCache()
