from fastapi import APIRouter

from api.health import router as health_router
from api.news_router import router as news_router
from api.invest_router import router as invest_router

router = APIRouter()

router.include_router(health_router)
router.include_router(news_router, prefix="/news", tags=["news"])
router.include_router(invest_router, prefix="/invest", tags=["invest"])