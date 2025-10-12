import redis
import os
from typing import Optional

class RedisClient:
    def __init__(self):
        # 환경 변수에서 Redis 설정을 가져오되, yh-auth 설정과 충돌하지 않도록 독립적으로 처리
        self.redis_host = "localhost"
        self.redis_port = 6379
        self.redis_db = 0
        self.redis_password = None
        
        self.client = redis.Redis(
            host=self.redis_host,
            port=self.redis_port,
            db=self.redis_db,
            password=self.redis_password,
            decode_responses=True
        )
    
    def get(self, key: str) -> Optional[str]:
        """키에 해당하는 값을 가져옵니다."""
        return self.client.get(key)
    
    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """키-값을 저장합니다. ex는 만료시간(초)입니다."""
        return self.client.set(key, value, ex=ex)
    
    def delete(self, key: str) -> bool:
        """키를 삭제합니다."""
        return bool(self.client.delete(key))
    
    def exists(self, key: str) -> bool:
        """키가 존재하는지 확인합니다."""
        return bool(self.client.exists(key))
    
    def expire(self, key: str, seconds: int) -> bool:
        """키의 만료시간을 설정합니다."""
        return bool(self.client.expire(key, seconds))
    
    def ping(self) -> bool:
        """Redis 연결을 테스트합니다."""
        try:
            return self.client.ping()
        except:
            return False

# 전역 Redis 클라이언트 인스턴스
redis_client = RedisClient()
