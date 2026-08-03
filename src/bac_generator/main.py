from fastapi import FastAPI

from bac_generator.api.routes.health import router
from bac_generator.core.config import settings

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

app.include_router(router)