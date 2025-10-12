# Arbitrage Trading Platform

차익거래 플랫폼 백엔드 API 서비스

## 프로젝트 구조

```
abitrage/
├── app/
│   ├── main.py              # FastAPI 메인 애플리케이션
│   ├── db/                  # 데이터베이스 관련 모듈
│   │   └── redis/           # Redis 관련 모듈
│   │       ├── redis_service.py    # Spring Boot 스타일 Redis 서비스
│   │       ├── redis_manager.py    # Redis 연결 관리자
│   │       └── redis_client.py     # Redis 클라이언트
│   └── collector/           # 거래소 데이터 수집 모듈
│       ├── base_exchange.py # 거래소 추상화 인터페이스
│       └── binance/         # Binance 거래소 모듈
│           └── binance_worker.py
├── data/
│   ├── postgres/            # PostgreSQL 데이터 디렉터리
│   └── redis/               # Redis 데이터 디렉터리
├── venv/                    # Python 가상 환경
├── docker-compose.yml       # Docker Compose 설정
├── requirements.txt         # Python 의존성
└── README.md
```

## 기술 스택

- **FastAPI**: 고성능 웹 프레임워크
- **PostgreSQL**: 데이터베이스
- **Redis**: 캐싱 및 pub/sub 메시징
- **yh-auth**: 인증/인가 라이브러리 (별도 레포지토리)
- **SQLAlchemy**: ORM
- **JWT**: 토큰 기반 인증
- **python-binance**: Binance API 클라이언트
- **WebSocket**: 실시간 데이터 스트리밍

## 설치 및 실행

### 1. 가상환경 설정

```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

requirements.txt는 yh-auth 라이브러리를 editable 모드로 설치합니다:
```
-e /Users/youngho/lts-project/base/yh-auth
```

### 3. 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=abitrage_db
POSTGRES_PORT=5432
POSTGRES_HOST=localhost

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_TIME=60
ACCESS_TOKEN_EXPIRE_DAYS=14
REFRESH_TOKEN_EXPIRE_DAYS=30
```

### 4. 데이터베이스 및 Redis 실행

Docker Compose를 사용하여 PostgreSQL과 Redis를 실행합니다:

```bash
docker-compose up -d
```

### 5. 데이터베이스 테이블 생성

```bash
python -c "
from yh_auth.database import engine
from yh_auth.user.models.user_models import Base
Base.metadata.create_all(engine)
print('데이터베이스 테이블 생성 완료')
"
```

### 6. 애플리케이션 실행

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API 문서

애플리케이션 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 주요 엔드포인트

### 인증 (yh-auth 라이브러리 제공)

- `POST /api/v1/auth/signup` - 회원가입
- `POST /api/v1/auth/login` - 로그인
- `POST /api/v1/auth/refresh` - 토큰 갱신

### 거래

- `GET /api/v1/trading/orders` - 거래 주문 조회 (인증 필요)
- `GET /api/v1/trading/positions` - 거래 포지션 조회 (인증 필요)

### Redis 캐시

- `GET /health/redis` - Redis 연결 상태 확인
- `GET /api/v1/cache/test` - Redis 캐시 테스트
- `GET /api/v1/cache/user/{user_id}` - 사용자별 캐시 데이터 (인증 필요)

### 거래소 데이터 수집

- `GET /api/v1/exchanges` - 지원하는 거래소 목록
- `GET /api/v1/exchanges/{exchange}/status` - 거래소 상태 조회
- `POST /api/v1/exchanges/{exchange}/subscribe` - 거래소 데이터 구독
- `GET /api/v1/redis/channels` - Redis pub/sub 채널 목록
- `GET /api/v1/redis/subscribe/{exchange}/{data_type}` - Redis 채널 구독 테스트

## yh-auth 라이브러리

이 프로젝트는 인증/인가 기능을 위해 `yh-auth` 라이브러리를 사용합니다.

- GitHub: https://github.com/Cha-Young-Ho/yh-auth
- 로컬 경로: `/Users/youngho/lts-project/base/yh-auth`

### 사용 예시

```python
from yh_auth import get_current_active_user
from yh_auth.auth_routes import router as auth_router

# 라우터 등록
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])

# 인증이 필요한 엔드포인트
@app.get("/protected")
def protected_route(current_user = Depends(get_current_active_user)):
    return {"message": f"Hello, {current_user.email}"}
```

## 거래소 데이터 수집 아키텍처

### Redis 연결 관리

- **단순 조회용**: 연결 풀을 사용한 공유 연결 (성능 최적화)
- **pub/sub용**: 거래소별 독립 연결 (안정성 보장)

### 지원하는 거래소

- **Binance**: WebSocket을 통한 실시간 데이터 수집
  - 티커 데이터 (24hr 통계)
  - 오더북 데이터 (5레벨)
  - 거래 내역
  - 캔들 데이터 (다양한 시간 간격)

### 데이터 타입

- `ticker`: 24시간 가격 통계
- `orderbook`: 호가창 데이터
- `trade`: 실시간 거래 내역
- `kline`: 캔들/봉 데이터
- `depth`: 시장 깊이 정보

### 사용 예시

```python
# Spring Boot 스타일 의존성 주입
from app.db.redis import redis_service, get_redis_client
from app.collector.binance.binance_worker import BinanceWorker

# FastAPI 엔드포인트에서 사용
@app.get("/api/example")
async def example_endpoint(redis_client = Depends(get_redis_client)):
    await redis_client.set("key", "value")
    return {"message": "Redis 자동 관리됨"}

# Binance Worker 생성
worker = BinanceWorker(redis_service)

# 데이터 구독
await worker.subscribe_ticker(["BTCUSDT", "ETHUSDT"])
await worker.subscribe_orderbook(["BTCUSDT"])

# Worker 시작
await worker.start()
```

## 개발

### 코드 스타일

- Python 3.8+
- PEP 8 준수
- Type hints 사용 권장

### 테스트

```bash
# Redis pub/sub 테스트
python test_binance_worker.py

# 전체 테스트
pytest
```

## 라이선스

MIT License
