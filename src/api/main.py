from fastapi import FastAPI

from src.api.routers import ai, analytics, auth, health, ml, pipeline


def create_app() -> FastAPI:
    app = FastAPI(
        title="Mercado Intelligence AI API",
        version="0.1.0",
        description="API para consumo dos marts analiticos e resultados de ML do Mercado Intelligence AI.",
    )
    app.include_router(health.router)
    app.include_router(analytics.router)
    app.include_router(ml.router)
    app.include_router(ai.router)
    app.include_router(auth.router)
    app.include_router(pipeline.router)
    return app


app = create_app()
