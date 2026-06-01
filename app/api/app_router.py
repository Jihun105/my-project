from fastapi import APIRouter

from api.health import router as health_router
from api.news_router import router as news_router
from api.invest_router import router as invest_router

router = APIRouter()



# ==========================================
# 하위 라우터 통합 및 서브 경로/태그 그룹화
# ==========================================

# 서버의 생존 여부를 모니터링하는 API(예: /health)는 보통 접두사(Prefix) 없이
router.include_router(health_router)

# prefix="/news" -> 이 라우터 안의 모든 URL 앞에 자동으로 `/news`가 붙습니다. (예: /news/list, /news/analyze)
# tags=["news"]  -> FastAPI의 Swagger 문서(/docs)에서 뉴스 관련 API들을 하나의 그룹으로 예쁘게 묶어 시각화해 줍니다.
router.include_router(news_router, prefix="/news", tags=["news"])

# 투자 관련 API들을 `/invest` 경로 아래로 격리하고, 문서상에 "invest" 그룹으로 분류
router.include_router(invest_router, prefix="/invest", tags=["invest"])