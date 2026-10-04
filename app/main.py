from __future__ import annotations

import logging
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from .agent import StudyPlannerAgent
from .config import get_settings
from .logging_config import configure_logging, request_id_context
from .models import ErrorResponse, HealthResponse, StudyPlanRequest, StudyPlanResponse

settings = get_settings()
configure_logging(settings.log_level, settings.log_file)
logger = logging.getLogger("app.http")
agent = StudyPlannerAgent()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="API cho AI agent lập kế hoạch học tập.",
)

# Expose request metrics for Prometheus and keep this operational endpoint out
# of the public OpenAPI schema.
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    token = request_id_context.set(request_id)
    started = time.perf_counter()
    logger.info(
        "request.started",
        extra={"event": "request.started", "method": request.method, "path": request.url.path},
    )
    try:
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request.completed",
            extra={
                "event": "request.completed",
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response
    except Exception:
        logger.exception(
            "request.failed",
            extra={
                "event": "request.failed",
                "method": request.method,
                "path": request.url.path,
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
            },
        )
        raise
    finally:
        request_id_context.reset(token)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(
        "request.validation_error",
        extra={"event": "request.validation_error", "path": request.url.path, "errors": exc.errors()},
    )
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "VALIDATION_ERROR", "message": "Dữ liệu đầu vào không hợp lệ."}},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "application.unhandled_exception",
        extra={"event": "application.unhandled_exception", "path": request.url.path},
    )
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "Đã xảy ra lỗi không mong muốn."}},
    )


@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.app_env,
        agent_mode="deterministic-tool-using",
    )


@app.post(
    "/api/v1/agent/study-plan",
    response_model=StudyPlanResponse,
    responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    tags=["agent"],
)
async def create_study_plan(payload: StudyPlanRequest) -> StudyPlanResponse:
    return agent.create_plan(payload)
