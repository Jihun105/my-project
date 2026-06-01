import os
from datetime import datetime

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from service.trend_service import analyze_trends

load_dotenv()

# Groq LLM 초기화
# temperature=0.3 = 창의성 낮추고 일관된 분석 결과 유도
llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.3-70b-versatile",
    temperature=0.3,
)

# 시스템 프롬프트
# LLM 에게 역할과 출력 형식을 지정
SYSTEM_PROMPT = """
당신은 전문 투자 분석가입니다.
뉴스 트렌드 데이터를 바탕으로 투자 가이드를 작성합니다.

반드시 아래 형식으로 작성하세요:

## 시장 요약
(전체 시장 상황 2~3줄 요약)

## 주목 섹터
(주목할 섹터와 이유)

## 종목 추천
(추천 종목과 근거, 최대 3개)

## 리스크 경고
(주의해야 할 리스크 요인)

## 면책 고지
본 리포트는 투자 참고용이며 실제 투자 손실에 대한 책임은 투자자 본인에게 있습니다.
"""


async def generate_invest_report() -> dict:
    """트렌드 분석 결과를 바탕으로 투자 가이드 생성"""

    # 1. 트렌드 분석
    print("트렌드 분석 중...")
    trend_data = await analyze_trends()

    if not trend_data["clusters"]:
        return {"error": "분석할 뉴스 데이터가 없습니다"}

    # 2. LLM 에 전달할 트렌드 요약 텍스트 생성
    trend_summary = _format_trend_for_llm(trend_data)

    # 3. Groq LLM 으로 투자 가이드 생성
    print("투자 가이드 생성 중...")
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"다음 뉴스 트렌드를 분석해서 투자 가이드를 작성해주세요:\n\n{trend_summary}"),
    ]

    response = await llm.ainvoke(messages)

    return {
        "report": response.content,
        "trend_data": trend_data,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def _format_trend_for_llm(trend_data: dict) -> str:
    """트렌드 데이터를 LLM 이 읽기 좋은 텍스트로 변환"""

    lines = []

    # 핫 섹터
    lines.append(f"## 주요 섹터: {', '.join(trend_data['hot_sectors'])}")
    lines.append("")

    # 클러스터별 트렌드
    lines.append("## 클러스터별 트렌드")
    for cluster in trend_data["clusters"]:
        lines.append(
            f"- [{cluster['sector']}] "
            f"뉴스 {cluster['news_count']}건 | "
            f"키워드: {', '.join(cluster['top_keywords'])}"
        )
        # 실제 뉴스 제목 목록 추가
        for title in cluster.get("top_titles", []):
            lines.append(f"  - {title}")

    return "\n".join(lines)