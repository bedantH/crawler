from redis import Redis
from typing import Optional

class RedisClient:
    _instance: Optional['RedisClient'] = None
    _redis: Optional[Redis] = None

    def __new__(cls, host: str = "localhost", port: int = 6379, db: int = 0):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._redis = Redis(host=host, port=port, db=db, decode_responses=True)
        return cls._instance

    def _check_connection(self) -> bool:
        """Returns True if Redis connection is initialized, False otherwise."""
        return self._redis is not None

    def set(self, key: str, value: str, ex: Optional[int] = None):
        if not self._check_connection():
            raise ConnectionError("Redis connection is not initialized.")
        self._redis.set(key, value, ex=ex)  #type: ignore

    def get(self, key: str) -> Optional[str]:
        if not self._check_connection():
            raise ConnectionError("Redis connection is not initialized.")
        return self._redis.get(key)  #type: ignore
    
    def ismember(self, key: str) -> bool:
        if not self._check_connection():
            raise ConnectionError("Redis connection is not initialized.")
        return self._redis.sismember(key) #type: ignore

    def delete(self, key: str):
        if not self._check_connection():
            raise ConnectionError("Redis connection is not initialized.")
        self._redis.delete(key)  #type: ignore

    def incr(self, key: str):
        if not self._check_connection():
            raise ConnectionError("Redis connection is not initialized.")
        return self._redis.incr(key)  #type: ignore

    def decr(self, key: str):
        if not self._check_connection():
            raise ConnectionError("Redis connection is not initialized.")
        return self._redis.decr(key)  #type: ignore

