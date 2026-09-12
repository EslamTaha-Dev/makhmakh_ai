from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.rate_limit import limiter

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.courses import router as courses_router
from app.api.routes.materials import router as materials_router
from app.api.routes.map import router as map_router
from app.api.routes.concepts import router as concepts_router
from app.api.routes.progress import router as progress_router
from app.api.routes.chat import router as chat_router
from app.api.routes.lessons import router as lessons_router
from app.api.routes.evaluation import router as evaluation_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.api.routes.admin import router as admin_router


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Bosla (بوصلة) — Educational AI Backend API",
)

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)



app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


register_exception_handlers(app)


app.include_router(health_router)

app.include_router(
    auth_router,
    prefix="/api/v1",
)
app.include_router(
    lessons_router,
    prefix="/api/v1",
)

app.include_router(
    courses_router,
    prefix="/api/v1",
)

app.include_router(
    materials_router,
    prefix="/api/v1",
)

app.include_router(
    map_router,
    prefix="/api/v1",
)

app.include_router(
    concepts_router,
    prefix="/api/v1",
)

app.include_router(
    progress_router,
    prefix="/api/v1",
)

app.include_router(
    chat_router,
    prefix="/api/v1",
)
app.include_router(
    evaluation_router,
    prefix="/api/v1",
)
app.include_router(
    admin_router,
    prefix="/api/v1",
)


@app.get("/")
def root():
    return {
        "message": "Bosla Backend is running",
        "version": settings.app_version,
    }