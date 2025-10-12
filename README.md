# Arbitrage Trading Platform

차익거래 플랫폼 백엔드 API 서비스

## 프로젝트 구조

```
abitrage/
├── app/
│   └── main.py              # FastAPI 메인 애플리케이션
├── data/
│   └── postgres/            # PostgreSQL 데이터 디렉터리
├── venv/                    # Python 가상 환경
├── docker-compose.yml       # Docker Compose 설정
├── requirements.txt         # Python 의존성
└── README.md
```

## 기술 스택

- **FastAPI**: 고성능 웹 프레임워크
- **PostgreSQL**: 데이터베이스
- **yh-auth**: 인증/인가 라이브러리 (별도 레포지토리)
- **SQLAlchemy**: ORM
- **JWT**: 토큰 기반 인증

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

### 4. 데이터베이스 실행

Docker Compose를 사용하여 PostgreSQL을 실행합니다:

```bash
docker-compose up -d
```

### 5. 애플리케이션 실행

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

## 개발

### 코드 스타일

- Python 3.8+
- PEP 8 준수
- Type hints 사용 권장

### 테스트

```bash
pytest
```

## 라이선스

MIT License
