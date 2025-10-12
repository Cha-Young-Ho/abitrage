from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

# yh-auth 라이브러리 import
from yh_auth import get_current_active_user
from yh_auth.database import get_db
from yh_auth.config import settings
from yh_auth.auth_routes import router as auth_router

# yh-db 라이브러리 import (Spring Boot 스타일)
from yh_db import db_manager, get_redis, get_postgres

# 거래소 worker import
from .collector.binance.binance_worker import BinanceWorker
from .collector.base_exchange import ExchangeType, DataType

app = FastAPI(
    title="Arbitrage Platform",
    version="1.0.0",
    description="Arbitrage Trading Platform with Authentication"
)

# 애플리케이션 시작/종료 이벤트 (Spring Boot 스타일)
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 yh-db 초기화"""
    await db_manager.initialize()
    print("🚀 yh-db 초기화 완료")

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 yh-db 연결 정리"""
    await db_manager.close_all()
    print("🛑 yh-db 정리 완료")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# yh-auth 라우터 등록
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])

@app.get("/")
def read_root():
    return {"message": "Arbitrage Platform API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/health/database")
async def database_health_check():
    """모든 데이터베이스 연결 상태를 확인합니다."""
    health_status = await db_manager.health_check()
    return {
        "message": "yh-db 상태 확인",
        "databases": health_status
    }

# 거래 관련 라우터 (인증 필요)
@app.get("/api/v1/trading/orders")
def get_trading_orders(current_user = Depends(get_current_active_user)):
    """거래 주문 조회 (인증 필요)"""
    return {
        "message": f"Trading orders for user: {current_user.email}",
        "user_id": current_user.id,
        "orders": []
    }

@app.get("/api/v1/trading/positions")
def get_trading_positions(current_user = Depends(get_current_active_user)):
    """거래 포지션 조회 (인증 필요)"""
    return {
        "message": f"Trading positions for user: {current_user.email}",
        "user_id": current_user.id,
        "positions": []
    }

@app.get("/api/v1/cache/test")
async def test_redis_cache(redis = Depends(get_redis)):
    """Redis 캐시 테스트 엔드포인트 (yh-db 사용)"""
    if not redis:
        return {"error": "Redis가 설정되지 않았습니다"}
    
    # 캐시에 데이터 저장
    await redis.set("test_key", "Hello yh-db!", ex=60)
    
    # 캐시에서 데이터 조회
    cached_value = await redis.get("test_key")
    
    return {
        "message": "yh-db Redis cache test",
        "cached_value": cached_value,
        "redis_connected": await redis.ping()
    }

@app.get("/api/v1/cache/user/{user_id}")
async def get_user_cache(user_id: int, current_user = Depends(get_current_active_user), redis = Depends(get_redis)):
    """사용자별 캐시 데이터 조회/저장 (yh-db 사용)"""
    if not redis:
        return {"error": "Redis가 설정되지 않았습니다"}
    
    cache_key = f"user:{user_id}:profile"
    
    # 캐시에서 조회 시도
    cached_data = await redis.get(cache_key)
    
    if cached_data:
        return {
            "message": "Data from cache",
            "user_id": user_id,
            "cached_data": cached_data,
            "source": "redis_cache"
        }
    else:
        # 캐시에 없으면 새로 생성하고 저장
        user_data = {
            "user_id": user_id,
            "email": current_user.email,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        # 5분간 캐시에 저장
        await redis.set(cache_key, str(user_data), ex=300)
        
        return {
            "message": "Data created and cached",
            "user_id": user_id,
            "data": user_data,
            "source": "database"
        }

# 거래소 데이터 수집 관련 API
@app.get("/api/v1/exchanges")
def get_exchanges():
    """지원하는 거래소 목록 조회"""
    return {
        "exchanges": [
            {"name": "binance", "type": ExchangeType.BINANCE.value, "status": "available"},
            {"name": "upbit", "type": ExchangeType.UPBIT.value, "status": "coming_soon"},
            {"name": "bithumb", "type": ExchangeType.BITHUMB.value, "status": "coming_soon"},
        ]
    }

@app.get("/api/v1/exchanges/{exchange}/status")
def get_exchange_status(exchange: str):
    """거래소 상태 조회"""
    if exchange == "binance":
        return {
            "exchange": exchange,
            "status": "available",
            "supported_data_types": [dt.value for dt in DataType],
            "redis_channels": {
                "ticker": f"{exchange}:ticker",
                "orderbook": f"{exchange}:orderbook",
                "trade": f"{exchange}:trade",
                "kline": f"{exchange}:kline"
            }
        }
    else:
        return {
            "exchange": exchange,
            "status": "not_implemented",
            "message": f"{exchange} 거래소는 아직 구현되지 않았습니다"
        }

@app.post("/api/v1/exchanges/{exchange}/subscribe")
def subscribe_exchange_data(exchange: str, symbols: list, data_types: list = ["ticker"]):
    """거래소 데이터 구독"""
    if exchange == "binance":
        # 실제로는 백그라운드 태스크로 worker를 시작해야 함
        return {
            "message": f"{exchange} 거래소 {symbols} 심볼의 {data_types} 데이터 구독 요청",
            "exchange": exchange,
            "symbols": symbols,
            "data_types": data_types,
            "status": "requested"
        }
    else:
        return {
            "error": f"{exchange} 거래소는 지원되지 않습니다",
            "supported_exchanges": ["binance"]
        }

@app.get("/api/v1/redis/channels")
async def get_redis_channels(redis = Depends(get_redis)):
    """Redis pub/sub 채널 목록 조회 (yh-db 사용)"""
    if not redis:
        return {"error": "Redis가 설정되지 않았습니다"}
    
    return {
        "channels": {
            "binance": {
                "ticker": "binance:ticker",
                "orderbook": "binance:orderbook", 
                "trade": "binance:trade",
                "kline": "binance:kline"
            }
        },
        "active_subscribers": len(redis._subscribers)
    }

@app.get("/api/v1/redis/subscribe/{exchange}/{data_type}")
async def subscribe_redis_channel(exchange: str, data_type: str, redis = Depends(get_redis)):
    """Redis 채널 구독 테스트 (yh-db 사용)"""
    if not redis:
        return {"error": "Redis가 설정되지 않았습니다"}
    
    try:
        channel = f"{exchange}:{data_type}"
        pubsub = await redis.subscribe(exchange, [channel])
        
        return {
            "message": f"Redis 채널 구독 성공",
            "exchange": exchange,
            "data_type": data_type,
            "channel": channel,
            "subscriber_count": len(redis._subscribers)
        }
    except Exception as e:
        return {
            "error": f"Redis 채널 구독 실패: {str(e)}"
        }

# yh-db 의존성 주입 예시
@app.get("/api/v1/yh-db/dependency-injection-example")
async def dependency_injection_example(
    redis = Depends(get_redis),
    postgres = Depends(get_postgres)
):
    """yh-db 의존성 주입 예시"""
    result = {
        "message": "yh-db 의존성 주입 성공",
        "databases": {}
    }
    
    # Redis 테스트
    if redis:
        await redis.set("yh_db_test", "Hello from yh-db!", ex=60)
        cached_value = await redis.get("yh_db_test")
        result["databases"]["redis"] = {
            "status": "connected",
            "cached_value": cached_value
        }
    else:
        result["databases"]["redis"] = {"status": "not_configured"}
    
    # PostgreSQL 테스트
    if postgres:
        is_connected = await postgres.ping()
        result["databases"]["postgres"] = {
            "status": "connected" if is_connected else "disconnected"
        }
    else:
        result["databases"]["postgres"] = {"status": "not_configured"}
    
    return result