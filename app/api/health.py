from fastapi import APIRouter

router = APIRouter()
# FastAPI에서 엔드포인트를 그룹으로 묶는 도구

@router.get("/health")
# /health 주소로 GET요청이 오면 아래 함수를 실행
async def health_check():
    return {"status": "ok", "message": "서버 정상 동작 중"}