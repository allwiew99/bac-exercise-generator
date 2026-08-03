from fastapi import FastAPI

from bac_generator.core.config import settings

app = FastAPI( 
    title=settings.app_name,
    debug=settings.debug,
      )


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}