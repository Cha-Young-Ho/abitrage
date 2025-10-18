from yh_auth import AuthManager, AuthParameters
from yh_db import MySQLManager
from yh_redis import RedisManager

class AuthService:
    def __init__(self, auth_manager: AuthManager, mysql_manager: MySQLManager, redis_manager: RedisManager):
        self.auth_manager = auth_manager
        self.mysql_manager = mysql_manager
        self.redis_manager = redis_manager

    # db 조회, 비번 Hash 비교 통과 시 토큰 발급
    def login(self, username: str, password: str):
        # 실제로는 MySQL에서 사용자 확인
        # user = self.mysql_manager.execute_query("SELECT * FROM users WHERE username = %s", [username])
        
        # 임시로 AuthParameters 생성
        auth_params = AuthParameters(
            name=username,
            email=None,
            userId=1,
            role=None
        )
        
        # 토큰 발급
        access_token = self.auth_manager.getAccessToken(auth_params)
        
        # Redis에 세션 저장 (예시)
        # self.redis_manager.set(f"session:{username}", access_token)
        
        return access_token