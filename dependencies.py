from fastapi import Depends
from yh_config import ConfigManager
from yh_auth import AuthManager, AuthConfig
from yh_redis import RedisManager, RedisConfig
from yh_mysql import MySQLManager, MySQLConfig
from src.auth.auth_service import AuthService
from functools import lru_cache

@lru_cache()
def get_config_manager():
    """LRU 캐시를 사용한 ConfigManager (업계 표준)"""
    return ConfigManager("config.yaml")

@lru_cache()
def get_auth_manager():
    """LRU 캐시를 사용한 AuthManager (업계 표준)"""
    config = get_config_manager()
    auth_config = AuthConfig(
        accessSecretKey=config.get_config("jwt")["access_secret"],
        refreshSecretKey=config.get_config("jwt")["refresh_secret"]
    )
    return AuthManager(auth_config)

@lru_cache()
def get_redis_manager():
    """LRU 캐시를 사용한 RedisManager (업계 표준)"""
    config = get_config_manager()
    redis_config_data = config.get_config("redis")
    redis_config = RedisConfig(
        host=redis_config_data["host"],
        port=redis_config_data["port"],
        db=redis_config_data["db"],
        decode_responses=redis_config_data["decode_responses"]
    )
    return RedisManager(redis_config)

@lru_cache()
def get_mysql_manager():
    """LRU 캐시를 사용한 MySQLManager (업계 표준)"""
    config = get_config_manager()
    mysql_config_data = config.get_config("database")
    mysql_config = MySQLConfig(
        dbNameKey="database",
        host=mysql_config_data["host"],
        port=mysql_config_data["port"],
        user=mysql_config_data["username"],
        password=mysql_config_data["password"],
        database=mysql_config_data["database"]
    )
    return MySQLManager(mysql_config)

@lru_cache()
def get_auth_service():
    """LRU 캐시를 사용한 AuthService (업계 표준)"""
    auth_manager = get_auth_manager()
    mysql_manager = get_mysql_manager()
    redis_manager = get_redis_manager()
    return AuthService(auth_manager, mysql_manager, redis_manager)
