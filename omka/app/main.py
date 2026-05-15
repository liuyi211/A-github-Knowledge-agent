from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from omka.app.core.config import settings
from omka.app.core.logging import logger
from omka.app.core.settings_service import init_default_settings
from omka.app.storage.db import init_db
from omka.app.storage.repositories import load_profile_sources


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("OMKA 启动中 | 版本=%s | 环境=%s", settings.app_version, settings.app_env)

    init_db()

    try:
        init_default_settings()
    except Exception as e:
        logger.warning("初始化默认配置失败 | error=%s", e)

    loaded = load_profile_sources()
    if loaded > 0:
        logger.info("从配置文件加载 %d 个数据源", loaded)

    logger.info("OMKA 启动完成 | API=http://%s:%d", settings.api_host, settings.api_port)

    yield

    logger.info("OMKA 已关闭")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Oh My Knowledge Assistant - 个人智能知识助手",
    lifespan=lifespan,
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from omka.app.api.middleware import APILoggingMiddleware
app.add_middleware(APILoggingMiddleware)


@app.get("/health", tags=["系统"])
async def health_check():
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "env": settings.app_env,
    }


from omka.app.api import routes_sources
app.include_router(routes_sources.router, prefix="/sources", tags=["信息源"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "omka.app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        reload=settings.debug,
    )
