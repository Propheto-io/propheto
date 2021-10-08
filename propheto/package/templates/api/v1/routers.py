from fastapi import APIRouter
from .endpoints import model, alerts, logs

router = APIRouter()

router.include_router(model.router, tags=["ML Models"])
router.include_router(alerts.router, tags=["alerts"])
router.include_router(logs.router, tags=["logs"])
