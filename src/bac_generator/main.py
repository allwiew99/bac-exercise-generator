from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bac_generator.api.exception_handlers import register_exception_handlers
from bac_generator.api.middleware import RequestIDMiddleware
from bac_generator.api.routes.exercises import router as exercises_router
from bac_generator.api.routes.health import router as health_router
from bac_generator.core.config import settings
from bac_generator.core.firebase import initialize_firebase
from bac_generator.core.logging_config import configure_logging

configure_logging()
initialize_firebase()


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)


app.add_middleware(
    RequestIDMiddleware,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "OPTIONS",
    ],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Request-ID",
    ],
    expose_headers=[
        "X-Request-ID",
    ],
)


register_exception_handlers(app)


app.include_router(exercises_router)
app.include_router(health_router)