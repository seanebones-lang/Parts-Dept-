from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from loguru import logger
import sys

from backend.config import settings
from backend.api import inventory, orders, email_routes, health
from backend.graph.connection import graph_db
from backend.rag.vectorstore import vector_store

logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.log_level
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Parts Department System")
    
    try:
        await graph_db.connect()
        logger.info("Neo4j connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
    
    try:
        await vector_store.initialize()
        logger.info("Qdrant initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Qdrant: {e}")
    
    yield
    
    logger.info("Shutting down Parts Department System")
    await graph_db.close()
    logger.info("Neo4j connection closed")


app = FastAPI(
    title="Parts Department System",
    description="Auto Dealer RAG + Graph System for Inventory and Email Automation",
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


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error handler caught: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )


app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(inventory.router, prefix="/api/v1/inventory", tags=["Inventory"])
app.include_router(orders.router, prefix="/api/v1/orders", tags=["Orders"])
app.include_router(email_routes.router, prefix="/api/v1/email", tags=["Email"])


@app.get("/")
async def root():
    return {
        "service": "Parts Department System",
        "version": "1.0.0",
        "status": "operational"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development"
    )

