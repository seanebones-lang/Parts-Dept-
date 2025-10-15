from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "parts-dept-system"
    }


@router.get("/ready")
async def readiness_check():
    return {
        "status": "ready",
        "components": {
            "api": "operational",
            "database": "operational",
            "graph": "operational",
            "vector_store": "operational"
        }
    }

