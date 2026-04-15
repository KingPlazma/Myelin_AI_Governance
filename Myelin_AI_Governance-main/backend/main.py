try:
    from backend.api_server_enhanced import app
except ImportError:
    from api_server_enhanced import app

if __name__ == "__main__":
    import uvicorn
    from config.settings import settings
    
    host = settings.API_HOST if settings.DEBUG else "127.0.0.1"
    uvicorn.run(
        "main:app",
        host=host,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        timeout_keep_alive=30,
    )
