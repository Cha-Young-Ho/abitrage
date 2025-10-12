# Arbitrage Trading Platform

차익거래 플랫폼 백엔드 API 서비스 - Spring Boot 스타일의 데이터베이스 관리와 FastAPI를 결합한 고성능 거래 플랫폼

## 🚀 주요 특징

- **Spring Boot 스타일 데이터베이스 관리**: `yh-db` 라이브러리를 통한 자동 연결 풀 관리
- **다중 데이터베이스 지원**: PostgreSQL, MySQL, Redis, DynamoDB 선택적 초기화
- **FastAPI 의존성 주입**: `Depends`를 통한 깔끔한 데이터베이스 클라이언트 주입
- **실시간 거래소 데이터**: WebSocket을 통한 Binance 실시간 데이터 수집
- **JWT 인증**: `yh-auth` 라이브러리를 통한 안전한 인증/인가
- **Redis Pub/Sub**: 거래소별 독립 연결을 통한 안정적인 메시징

## 📁 프로젝트 구조

```
abitrage/
├── app/
│   ├── main.py              # FastAPI 메인 애플리케이션
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

## 🛠 기술 스택

- **FastAPI**: 고성능 웹 프레임워크
- **yh-db**: 통합 데이터베이스 관리 라이브러리 (Spring Boot 스타일)
- **yh-auth**: JWT 인증/인가 라이브러리
- **PostgreSQL**: 메인 데이터베이스
- **Redis**: 캐싱 및 pub/sub 메시징
- **SQLAlchemy**: ORM
- **python-binance**: Binance API 클라이언트
- **WebSocket**: 실시간 데이터 스트리밍

## 🚀 빠른 시작

### 1. 가상환경 설정

```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

`requirements.txt`는 GitHub에서 `yh-auth`와 `yh-db` 라이브러리를 자동으로 설치합니다:
```
yh-auth @ git+https://github.com/Cha-Young-Ho/yh-auth.git
yh-db @ git+https://github.com/Cha-Young-Ho/yh-db.git
```

### 3. 데이터베이스 및 Redis 실행

Docker Compose를 사용하여 PostgreSQL과 Redis를 실행합니다:

```bash
docker-compose up -d
```

### 4. 데이터베이스 생성

```bash
# PostgreSQL에 test_db 데이터베이스 생성
docker exec -it abitrage-postgres-1 psql -U postgres -c "CREATE DATABASE test_db;"
```

### 5. 애플리케이션 실행

**기본 실행 (PostgreSQL + Redis):**
```bash
ENABLED_DATABASES=postgres,redis JWT_SECRET_KEY=test-secret-key POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_USER=postgres POSTGRES_PASSWORD=password POSTGRES_DB=test_db uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**개발 모드 (자동 재시작):**
```bash
ENABLED_DATABASES=postgres,redis JWT_SECRET_KEY=test-secret-key POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_USER=postgres POSTGRES_PASSWORD=password POSTGRES_DB=test_db uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## ⚙️ 환경 변수 설정

### 필수 환경 변수

```bash
# 사용할 데이터베이스 선택 (쉼표로 구분)
ENABLED_DATABASES=postgres,redis

# JWT 인증
JWT_SECRET_KEY=your-secret-key-here

# PostgreSQL 설정
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=test_db

# Redis 설정 (기본값 사용)
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 선택적 환경 변수

```bash
# MySQL 설정 (ENABLED_DATABASES에 mysql 포함 시)
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=password
MYSQL_DB=my_database

# DynamoDB 설정 (ENABLED_DATABASES에 dynamodb 포함 시)
DYNAMODB_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
```

## 📚 API 문서

애플리케이션 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔗 주요 엔드포인트

### 🏥 헬스체크

- `GET /health` - 기본 헬스체크
- `GET /api/v1/health/database` - 모든 데이터베이스 연결 상태 확인

### 🔐 인증 (yh-auth 라이브러리 제공)

- `POST /api/v1/auth/signup` - 회원가입
- `POST /api/v1/auth/login` - 로그인
- `POST /api/v1/auth/refresh` - 토큰 갱신

### 💼 거래

- `GET /api/v1/trading/orders` - 거래 주문 조회 (인증 필요)
- `GET /api/v1/trading/positions` - 거래 포지션 조회 (인증 필요)

### 🗄️ yh-db 데이터베이스 관리

- `GET /api/v1/cache/test` - Redis 캐시 테스트
- `GET /api/v1/cache/user/{user_id}` - 사용자별 캐시 데이터 (인증 필요)
- `GET /api/v1/yh-db/dependency-injection-example` - yh-db 의존성 주입 예시

### 📊 거래소 데이터 수집

- `GET /api/v1/exchanges` - 지원하는 거래소 목록
- `GET /api/v1/exchanges/{exchange}/status` - 거래소 상태 조회
- `POST /api/v1/exchanges/{exchange}/subscribe` - 거래소 데이터 구독
- `GET /api/v1/redis/channels` - Redis pub/sub 채널 목록
- `GET /api/v1/redis/subscribe/{exchange}/{data_type}` - Redis 채널 구독 테스트

## 📦 사용된 라이브러리

### yh-auth (JWT 인증/인가)

- **GitHub**: https://github.com/Cha-Young-Ho/yh-auth
- **기능**: JWT 토큰 기반 인증, 회원가입, 로그인, 토큰 갱신

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

### yh-db (통합 데이터베이스 관리)

- **GitHub**: https://github.com/Cha-Young-Ho/yh-db
- **기능**: Spring Boot 스타일의 자동 데이터베이스 연결 관리

```python
from yh_db import db_manager, get_redis, get_postgres

# 애플리케이션 시작/종료 시 자동 관리
@app.on_event("startup")
async def startup_event():
    await db_manager.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    await db_manager.close_all()

# FastAPI 의존성 주입
@app.get("/api/example")
async def example_endpoint(
    redis = Depends(get_redis),
    postgres = Depends(get_postgres)
):
    # Redis 사용
    await redis.set("key", "value")
    
    # PostgreSQL 사용
    result = await postgres.fetch_all("SELECT * FROM users")
    return {"data": result}
```

## 📊 거래소 데이터 수집 아키텍처

### 🔗 Redis 연결 관리

- **단순 조회용**: 연결 풀을 사용한 공유 연결 (성능 최적화)
- **pub/sub용**: 거래소별 독립 연결 (안정성 보장)

### 🏢 지원하는 거래소

- **Binance**: WebSocket을 통한 실시간 데이터 수집
  - 티커 데이터 (24hr 통계)
  - 오더북 데이터 (5레벨)
  - 거래 내역
  - 캔들 데이터 (다양한 시간 간격)

### 📈 데이터 타입

- `ticker`: 24시간 가격 통계
- `orderbook`: 호가창 데이터
- `trade`: 실시간 거래 내역
- `kline`: 캔들/봉 데이터
- `depth`: 시장 깊이 정보

### 💡 사용 예시

```python
# yh-db를 통한 의존성 주입
from yh_db import get_redis
from app.collector.binance.binance_worker import BinanceWorker

# FastAPI 엔드포인트에서 사용
@app.get("/api/example")
async def example_endpoint(redis = Depends(get_redis)):
    await redis.set("key", "value")
    return {"message": "Redis 자동 관리됨"}

# Binance Worker 생성
worker = BinanceWorker(redis)

# 데이터 구독
await worker.subscribe_ticker(["BTCUSDT", "ETHUSDT"])
await worker.subscribe_orderbook(["BTCUSDT"])

# Worker 시작
await worker.start()
```

## 🧪 테스트

### API 테스트

```bash
# 기본 헬스체크
curl http://localhost:8000/health

# 데이터베이스 상태 확인
curl http://localhost:8000/api/v1/health/database

# Redis 캐시 테스트
curl http://localhost:8000/api/v1/cache/test

# yh-db 의존성 주입 테스트
curl http://localhost:8000/api/v1/yh-db/dependency-injection-example
```

### 인증 테스트

```bash
# 회원가입
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpassword"}'

# 로그인
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpassword"}'
```

## 🛠 개발

### 코드 스타일

- Python 3.8+
- PEP 8 준수
- Type hints 사용 권장

### 환경 변수 관리

```bash
# .env 파일 생성 (선택사항)
cat > .env << EOF
ENABLED_DATABASES=postgres,redis
JWT_SECRET_KEY=your-secret-key-here
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=test_db
EOF
```

## 📄 라이선스

MIT License
