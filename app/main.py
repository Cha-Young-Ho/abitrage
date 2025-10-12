from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

# yh-auth 라이브러리 import
from yh_auth import get_current_active_user
from yh_auth.database import get_db
from yh_auth.config import settings
from yh_auth.auth_routes import router as auth_router

app = FastAPI(
    title="Arbitrage Platform",
    version="1.0.0",
    description="Arbitrage Trading Platform with Authentication"
)

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