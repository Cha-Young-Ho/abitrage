"""
Redis 매니저 - 연결 풀링 및 pub/sub 관리
- 단순 조회용: 단일 연결 풀 공유
- pub/sub용: 거래소별 독립 연결
"""
import redis
import asyncio
from typing import Dict, Optional, Any, List
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

class RedisManager:
    """Redis 연결 관리자"""
    
    def __init__(self):
        self.redis_host = "localhost"
        self.redis_port = 6379
        self.redis_db = 0
        
        # 단순 조회용 연결 풀 (공유)
        self._read_pool = None
        
        # pub/sub용 연결 (거래소별 독립)
        self._pubsub_connections: Dict[str, redis.Redis] = {}
        
        # pub/sub 구독 관리
        self._subscribers: Dict[str, redis.client.PubSub] = {}
        
        self._initialize_connections()
    
    def _initialize_connections(self):
        """연결 초기화"""
        try:
            # 단순 조회용 연결 풀 생성
            self._read_pool = redis.ConnectionPool(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                max_connections=20,
                decode_responses=True
            )
            
            logger.info(f"Redis 연결 풀 초기화 완료: {self.redis_host}:{self.redis_port}")
            
        except Exception as e:
            logger.error(f"Redis 연결 초기화 실패: {e}")
            raise
    
    def get_read_client(self) -> redis.Redis:
        """단순 조회용 Redis 클라이언트 반환 (연결 풀 사용)"""
        if not self._read_pool:
            raise RuntimeError("Redis 연결 풀이 초기화되지 않았습니다")
        
        return redis.Redis(connection_pool=self._read_pool)
    
    def get_pubsub_client(self, exchange: str) -> redis.Redis:
        """거래소별 pub/sub용 Redis 클라이언트 반환"""
        if exchange not in self._pubsub_connections:
            # 거래소별 독립 연결 생성
            self._pubsub_connections[exchange] = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                decode_responses=True
            )
            logger.info(f"{exchange} 거래소용 pub/sub 연결 생성")
        
        return self._pubsub_connections[exchange]
    
    def publish(self, exchange: str, channel: str, message: Any) -> bool:
        """메시지 발행"""
        try:
            client = self.get_pubsub_client(exchange)
            result = client.publish(channel, message)
            logger.debug(f"{exchange}:{channel}에 메시지 발행 - {message}")
            return result > 0
        except Exception as e:
            logger.error(f"메시지 발행 실패 {exchange}:{channel}: {e}")
            return False
    
    def subscribe(self, exchange: str, channels: List[str]) -> redis.client.PubSub:
        """채널 구독"""
        try:
            client = self.get_pubsub_client(exchange)
            pubsub = client.pubsub()
            pubsub.subscribe(*channels)
            
            # 구독자 등록
            subscriber_key = f"{exchange}:{':'.join(channels)}"
            self._subscribers[subscriber_key] = pubsub
            
            logger.info(f"{exchange} 거래소 채널 구독: {channels}")
            return pubsub
            
        except Exception as e:
            logger.error(f"채널 구독 실패 {exchange}:{channels}: {e}")
            raise
    
    def unsubscribe(self, exchange: str, channels: List[str]):
        """채널 구독 해제"""
        try:
            subscriber_key = f"{exchange}:{':'.join(channels)}"
            if subscriber_key in self._subscribers:
                pubsub = self._subscribers[subscriber_key]
                pubsub.unsubscribe(*channels)
                pubsub.close()
                del self._subscribers[subscriber_key]
                logger.info(f"{exchange} 거래소 채널 구독 해제: {channels}")
        except Exception as e:
            logger.error(f"채널 구독 해제 실패 {exchange}:{channels}: {e}")
    
    def get_message(self, exchange: str, channels: List[str], timeout: float = 1.0) -> Optional[Dict]:
        """구독된 채널에서 메시지 수신"""
        try:
            subscriber_key = f"{exchange}:{':'.join(channels)}"
            if subscriber_key in self._subscribers:
                pubsub = self._subscribers[subscriber_key]
                message = pubsub.get_message(timeout=timeout)
                if message and message['type'] == 'message':
                    return {
                        'channel': message['channel'],
                        'data': message['data'],
                        'exchange': exchange
                    }
        except Exception as e:
            logger.error(f"메시지 수신 실패 {exchange}:{channels}: {e}")
        return None
    
    # 단순 조회 메서드들 (연결 풀 사용)
    def get(self, key: str) -> Optional[str]:
        """키 값 조회"""
        client = self.get_read_client()
        return client.get(key)
    
    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """키-값 저장"""
        client = self.get_read_client()
        return client.set(key, value, ex=ex)
    
    def delete(self, key: str) -> bool:
        """키 삭제"""
        client = self.get_read_client()
        return bool(client.delete(key))
    
    def exists(self, key: str) -> bool:
        """키 존재 여부 확인"""
        client = self.get_read_client()
        return bool(client.exists(key))
    
    def ping(self) -> bool:
        """연결 상태 확인"""
        try:
            client = self.get_read_client()
            return client.ping()
        except Exception:
            return False
    
    def close_all(self):
        """모든 연결 종료"""
        try:
            # pub/sub 구독자들 종료
            for pubsub in self._subscribers.values():
                pubsub.close()
            self._subscribers.clear()
            
            # pub/sub 연결들 종료
            for client in self._pubsub_connections.values():
                client.close()
            self._pubsub_connections.clear()
            
            # 읽기용 연결 풀 종료
            if self._read_pool:
                self._read_pool.disconnect()
                self._read_pool = None
            
            logger.info("모든 Redis 연결 종료 완료")
            
        except Exception as e:
            logger.error(f"Redis 연결 종료 중 오류: {e}")

# 전역 Redis 매니저 인스턴스
redis_manager = RedisManager()

# FastAPI 의존성 주입용 함수들
def get_redis_manager() -> RedisManager:
    """Redis 매니저 의존성 주입"""
    return redis_manager

def get_redis_read_client() -> redis.Redis:
    """단순 조회용 Redis 클라이언트 의존성 주입"""
    return redis_manager.get_read_client()

def get_redis_pubsub_client(exchange: str) -> redis.Redis:
    """거래소별 pub/sub용 Redis 클라이언트 의존성 주입"""
    return redis_manager.get_pubsub_client(exchange)
