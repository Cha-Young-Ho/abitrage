"""
Spring Boot 스타일 Redis 서비스
FastAPI 의존성 주입으로 자동 연결 풀 관리
"""
import redis.asyncio as redis
from redis.asyncio import Redis
from fastapi import Depends
from typing import Dict, List, Optional, Any
import asyncio
import logging

logger = logging.getLogger(__name__)

class RedisService:
    """Spring Boot 스타일 Redis 서비스"""
    
    def __init__(self):
        self._read_pool: Optional[Redis] = None
        self._pubsub_connections: Dict[str, Redis] = {}
        self._subscribers: Dict[str, redis.client.PubSub] = {}
    
    async def initialize(self):
        """서비스 초기화 (애플리케이션 시작 시 호출)"""
        try:
            # 단순 조회용 연결 풀 생성 (자동 관리)
            self._read_pool = redis.from_url(
                "redis://localhost:6379/0",
                encoding="utf-8",
                decode_responses=True,
                max_connections=20,
                retry_on_timeout=True
            )
            logger.info("✅ Redis 읽기용 연결 풀 초기화 완료")
            
        except Exception as e:
            logger.error(f"❌ Redis 초기화 실패: {e}")
            raise
    
    async def get_read_client(self) -> Redis:
        """단순 조회용 Redis 클라이언트 (연결 풀 자동 관리)"""
        if not self._read_pool:
            await self.initialize()
        return self._read_pool
    
    async def get_pubsub_client(self, exchange: str) -> Redis:
        """거래소별 pub/sub용 Redis 클라이언트 (자동 관리)"""
        if exchange not in self._pubsub_connections:
            # 거래소별 독립 연결 생성 (자동 관리)
            self._pubsub_connections[exchange] = redis.from_url(
                "redis://localhost:6379/0",
                encoding="utf-8",
                decode_responses=True,
                max_connections=5,
                retry_on_timeout=True
            )
            logger.info(f"✅ {exchange} 거래소용 pub/sub 연결 생성")
        
        return self._pubsub_connections[exchange]
    
    async def publish(self, exchange: str, channel: str, message: Any) -> bool:
        """메시지 발행 (자동 연결 관리)"""
        try:
            client = await self.get_pubsub_client(exchange)
            result = await client.publish(channel, message)
            logger.debug(f"📤 {exchange}:{channel}에 메시지 발행")
            return result > 0
        except Exception as e:
            logger.error(f"❌ 메시지 발행 실패 {exchange}:{channel}: {e}")
            return False
    
    async def subscribe(self, exchange: str, channels: List[str]) -> redis.client.PubSub:
        """채널 구독 (자동 연결 관리)"""
        try:
            client = await self.get_pubsub_client(exchange)
            pubsub = client.pubsub()
            await pubsub.subscribe(*channels)
            
            # 구독자 등록
            subscriber_key = f"{exchange}:{':'.join(channels)}"
            self._subscribers[subscriber_key] = pubsub
            
            logger.info(f"✅ {exchange} 거래소 채널 구독: {channels}")
            return pubsub
            
        except Exception as e:
            logger.error(f"❌ 채널 구독 실패 {exchange}:{channels}: {e}")
            raise
    
    async def get_message(self, exchange: str, channels: List[str], timeout: float = 1.0) -> Optional[Dict]:
        """구독된 채널에서 메시지 수신 (자동 관리)"""
        try:
            subscriber_key = f"{exchange}:{':'.join(channels)}"
            if subscriber_key in self._subscribers:
                pubsub = self._subscribers[subscriber_key]
                message = await pubsub.get_message(timeout=timeout)
                if message and message['type'] == 'message':
                    return {
                        'channel': message['channel'],
                        'data': message['data'],
                        'exchange': exchange
                    }
        except Exception as e:
            logger.error(f"❌ 메시지 수신 실패 {exchange}:{channels}: {e}")
        return None
    
    # 단순 조회 메서드들 (연결 풀 자동 관리)
    async def get(self, key: str) -> Optional[str]:
        """키 값 조회 (자동 연결 관리)"""
        client = await self.get_read_client()
        return await client.get(key)
    
    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """키-값 저장 (자동 연결 관리)"""
        client = await self.get_read_client()
        result = await client.set(key, value, ex=ex)
        return bool(result)
    
    async def delete(self, key: str) -> bool:
        """키 삭제 (자동 연결 관리)"""
        client = await self.get_read_client()
        result = await client.delete(key)
        return bool(result)
    
    async def exists(self, key: str) -> bool:
        """키 존재 여부 확인 (자동 연결 관리)"""
        client = await self.get_read_client()
        result = await client.exists(key)
        return bool(result)
    
    async def ping(self) -> bool:
        """연결 상태 확인 (자동 관리)"""
        try:
            client = await self.get_read_client()
            result = await client.ping()
            return result
        except Exception:
            return False
    
    async def close_all(self):
        """모든 연결 종료 (자동 정리)"""
        try:
            # pub/sub 구독자들 종료
            for pubsub in self._subscribers.values():
                await pubsub.close()
            self._subscribers.clear()
            
            # pub/sub 연결들 종료
            for client in self._pubsub_connections.values():
                await client.close()
            self._pubsub_connections.clear()
            
            # 읽기용 연결 풀 종료
            if self._read_pool:
                await self._read_pool.close()
                self._read_pool = None
            
            logger.info("✅ 모든 Redis 연결 자동 정리 완료")
            
        except Exception as e:
            logger.error(f"❌ Redis 연결 정리 중 오류: {e}")

# 전역 Redis 서비스 인스턴스
redis_service = RedisService()

# FastAPI 의존성 주입용 함수들 (Spring Boot 스타일)
async def get_redis_service() -> RedisService:
    """Redis 서비스 의존성 주입"""
    return redis_service

async def get_redis_client() -> Redis:
    """단순 조회용 Redis 클라이언트 의존성 주입 (자동 연결 관리)"""
    return await redis_service.get_read_client()

async def get_redis_pubsub_client(exchange: str) -> Redis:
    """거래소별 pub/sub용 Redis 클라이언트 의존성 주입 (자동 관리)"""
    return await redis_service.get_pubsub_client(exchange)
