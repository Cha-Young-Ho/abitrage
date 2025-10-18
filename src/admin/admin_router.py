from fastapi import APIRouter, Depends, HTTPException, status
from dependencies import get_config_manager, get_auth_manager, get_redis_manager, get_mysql_manager, get_auth_service

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/reload-config")
async def reload_config():
    """
    설정 파일을 다시 로드하고 모든 캐시를 클리어합니다.
    """
    try:
        # 모든 캐시 클리어
        get_config_manager.cache_clear()
        get_auth_manager.cache_clear()
        get_redis_manager.cache_clear()
        get_mysql_manager.cache_clear()
        get_auth_service.cache_clear()
        
        # 새 설정으로 인스턴스 생성하여 검증
        config = get_config_manager()
        auth_manager = get_auth_manager()
        redis_manager = get_redis_manager()
        mysql_manager = get_mysql_manager()
        auth_service = get_auth_service()
        
        return {
            "message": "설정이 성공적으로 리로드되었습니다",
            "status": "success",
            "reloaded_components": [
                "config_manager",
                "auth_manager", 
                "redis_manager",
                "mysql_manager",
                "auth_service"
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"설정 리로드 중 오류 발생: {str(e)}"
        )

@router.get("/config-status")
async def get_config_status():
    """
    현재 설정 상태를 확인합니다.
    """
    try:
        config = get_config_manager()
        
        jwt_config = config.get_config("jwt")
        redis_config = config.get_config("redis")
        database_config = config.get_config("database")
        api_config = config.get_config("api")
        
        return {
            "message": "설정 상태 조회 성공",
            "status": "success",
            "config_info": {
                "jwt_configured": bool(jwt_config.get("access_secret") if jwt_config else False),
                "redis_configured": bool(redis_config.get("host") if redis_config else False),
                "database_configured": bool(database_config.get("host") if database_config else False),
                "api_info": api_config
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"설정 상태 조회 중 오류 발생: {str(e)}"
        )

@router.post("/clear-cache")
async def clear_cache():
    """
    특정 컴포넌트의 캐시만 클리어합니다.
    """
    try:
        # 모든 캐시 클리어
        get_config_manager.cache_clear()
        get_auth_manager.cache_clear()
        get_redis_manager.cache_clear()
        get_mysql_manager.cache_clear()
        get_auth_service.cache_clear()
        
        return {
            "message": "캐시가 성공적으로 클리어되었습니다",
            "status": "success",
            "cleared_components": [
                "config_manager",
                "auth_manager",
                "redis_manager", 
                "mysql_manager",
                "auth_service"
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"캐시 클리어 중 오류 발생: {str(e)}"
        )
