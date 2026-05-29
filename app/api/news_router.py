from fastapi import APIRouter, HTTPException, Query

from service.news_service import collect_and_preprocess, get_news_list

router = APIRouter()


@router.post("/collect")
async def collect_news():
    """RSS 수집 + 임베딩 + 저장 수동 실행"""
    try:
        count = await collect_and_preprocess()
        return {
            "success": True,
            "message": f"{count}건 뉴스 수집 완료",
            "count": count,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def get_news(
    limit: int = Query(default=20, ge=1, le=100),
    sector: str = Query(default=None, description="섹터 필터 (예: 반도체, 금융)"),
):
    """저장된 뉴스 목록 조회"""
    try:
        items = await get_news_list(limit=limit, sector=sector)
        return {"items": items, "total": len(items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))