import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from service.invest_service import generate_invest_report
from service.agent_service import run_agent, run_agent_once

router = APIRouter()


@router.post("/report")
async def get_invest_report():
    """투자 가이드 리포트 생성"""
    try:
        report = await generate_invest_report()
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-pipeline")
async def run_full_pipeline():
    """전체 파이프라인 수동 실행 (수집 → 분석 → 리포트)"""
    try:
        result = await run_agent_once()
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream-pipeline")
async def stream_full_pipeline():
    """전체 파이프라인 스트리밍 실행"""

    async def event_generator():
        try:
            # 각 노드 완료될 때마다 결과를 SSE 형식으로 전송
            async for chunk in run_agent(stream=True):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            # 스트림 종료 신호
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )