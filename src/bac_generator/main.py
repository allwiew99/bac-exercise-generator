from fastapi import FastAPI

app = FastAPI(title="Bac Exercise Generator API")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}