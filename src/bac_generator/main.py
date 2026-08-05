from fastapi import FastAPI

from bac_generator.api.exception_handlers import register_exception_handlers
from bac_generator.api.routes.exercises import router as exercises_router
from bac_generator.api.routes.health import router as health_router
from bac_generator.core.config import settings
from bac_generator.core.logging_config import configure_logging

configure_logging()
app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)
register_exception_handlers(app)
app.include_router(exercises_router)
app.include_router(health_router)