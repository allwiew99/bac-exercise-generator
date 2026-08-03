from fastapi import FastAPI

from bac_generator.api.routes.exercises import router as exercises_router
from bac_generator.api.routes.health import router as health_router
from bac_generator.core.config import settings

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

app.include_router(exercises_router)
app.include_router(health_router)
