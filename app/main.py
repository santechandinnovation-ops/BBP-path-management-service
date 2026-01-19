from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.routes import paths, health
from app.config.database import init_db_pool, close_db_pool

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Path Management Service...")
    init_db_pool()
    yield
    logger.info("Shutting down Path Management Service...")
    close_db_pool()

app = FastAPI(
    title="BBP Path Management Service",
    description="Manages bike path information, route search, and obstacle reporting",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(paths.router, prefix="/paths", tags=["Paths"])
app.include_router(paths.router, prefix="/routes", tags=["Routes"])
app.include_router(health.router, tags=["Health"])

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error", "message": str(exc)}
    )

@app.get("/")
async def root():
    return {
        "service": "BBP Path Management Service",
        "version": "1.0.0",
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    from app.config.settings import settings

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=True
    )
