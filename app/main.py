import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Awaitable, Callable

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.config import get_settings
from app.core.client import LLMClient
from app.storage.memory import MemoryStorage
from app.utils.exceptions import AppException
from app.utils.logger import setup_logging

settings = get_settings()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager"""
    # Startup
    setup_logging(settings.log_level)
    logger.info("Starting LLM Call Center Agent", version=settings.app_version)

    # Initialize services
    llm_client = LLMClient()
    storage = MemoryStorage()

    # Store in app state
    app.state.llm_client = llm_client
    app.state.storage = storage

    logger.info("Application startup complete")
    yield

    # Shutdown
    logger.info("Shutting down application")
    await llm_client.close()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered call center automation agent",
    lifespan=lifespan,
    debug=settings.debug,
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def logging_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Request logging middleware"""
    start_time = time.time()

    # Log request
    client_ip = request.client.host if request.client else "unknown"
    logger.info(
        "Request started",
        method=request.method,
        path=request.url.path,
        client_ip=client_ip,
    )

    # Process request
    try:
        response = await call_next(request)
        duration = time.time() - start_time

        logger.info(
            "Request completed",
            status_code=response.status_code,
            duration=round(duration, 4),
        )

        return response
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            "Request failed",
            error=str(e),
            duration=round(duration, 4),
        )
        raise


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle application exceptions"""
    logger.error("Application error", error=str(exc), code=exc.code)

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
    )


app.include_router(api_router, prefix="/api")


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint"""
    return {"name": settings.app_name, "version": settings.app_version, "status": "running"}
