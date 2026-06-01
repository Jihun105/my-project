import os
from datetime import datetime

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from service.trend_service import analyze_trends
from infra.market_client import get_multiple_stocks

load_dotenv()

# Groq LLM 초기화
llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.3-70b-versatile",
    temperature=0.3,
)

# 시스템 프롬프트
SYSTEM_PROMPT = """
당신은 전문 투자 분석가입니다.
뉴스 트렌드 데이터와 실제 주가/재무 데이터를 바탕으로 투자 가이드를 작성합니다.

반드시 아래 형식으로 작성하세요:

## 시장 요약
(전체 시장 상황 2~3줄 요약)

## 주목 섹터
(주목할 섹터와 이유)

## 종목 추천
(추천 종목과 근거, 실제 주가/재무 데이터 기반으로 최대 3개)

## 리스크 경고
(주의해야 할 리스크 요인)

## 면책 고지
본 리포트는 투자 참고용이며 실제 투자 손실에 대한 책임은 투자자 본인에게 있습니다.
"""


async def generate_invest_report() -> dict:
    """트렌드 분석 + 주가 데이터를 바탕으로 투자 가이드 생성"""

    # 1. 트렌드 분석
    print("트렌드 분석 중...")
    trend_data = await analyze_trends()

    if not trend_data["clusters"]:
        return {"error": "분석할 뉴스 데이터가 없습니다"}

    # 2. 트렌드에서 언급된 종목명 추출
    company_names = _extract_company_names(trend_data)

    # 3. 주가 데이터 가져오기
    print(f"주가 데이터 조회 중... ({len(company_names)}개 종목)")
    stock_data = await get_multiple_stocks(company_names)

    # 4. LLM 에 전달할 트렌드 요약 텍스트 생성
    trend_summary = _format_trend_for_llm(trend_data, stock_data)

    # 5. Groq LLM 으로 투자 가이드 생성
    print("투자 가이드 생성 중...")
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"다음 뉴스 트렌드와 주가 데이터를 분석해서 투자 가이드를 작성해주세요:\n\n{trend_summary}"),
    ]

    response = await llm.ainvoke(messages)

    return {
        "report": response.content,
        "trend_data": trend_data,
        "stock_data": stock_data,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def _extract_company_names(trend_data: dict) -> list[str]:
    """트렌드 데이터에서 종목명 추출"""

    known_companies = [
        "삼성전자", "SK하이닉스", "LG에너지솔루션", "삼성SDI",
        "삼성전기", "NAVER", "카카오", "현대차", "기아",
        "POSCO홀딩스", "LG화학", "셀트리온", "코웨이",
        "KB금융", "신한지주", "하나금융지주", "토스뱅크",
    ]

    found = set()

    for cluster in trend_data["clusters"]:
        # 키워드에서 검색
        for keyword in cluster["top_keywords"]:
            for company in known_companies:
                if keyword in company or company in keyword:
                    found.add(company)

        # 뉴스 제목에서 검색
        for title in cluster.get("top_titles", []):
            for company in known_companies:
                if company in title:
                    found.add(company)

    return list(found)


def _format_trend_for_llm(trend_data: dict, stock_data: list[dict]) -> str:
    """트렌드 + 주가 데이터를 LLM 이 읽기 좋은 텍스트로 변환"""

    lines = []

    # 핫 섹터
    lines.append(f"## 주요 섹터: {', '.join(trend_data['hot_sectors'])}")
    lines.append("")

    # 클러스터별 트렌드 + 실제 뉴스 제목
    lines.append("## 클러스터별 트렌드")
    for cluster in trend_data["clusters"]:
        lines.append(
            f"\n### [{cluster['sector']}] "
            f"뉴스 {cluster['news_count']}건 | "
            f"키워드: {', '.join(cluster['top_keywords'])}"
        )
        for title in cluster.get("top_titles", []):
            lines.append(f"  - {title}")

    # 주가 데이터
    if stock_data:
        lines.append("\n## 관련 종목 주가 데이터")
        for stock in stock_data:
            lines.append(f"\n### {stock['name']} ({stock['ticker']})")
            lines.append(f"  - 현재가: {stock['current_price']:,}원")
            lines.append(f"  - 등락률: {stock['change_pct']}%")
            lines.append(f"  - 52주 최고가: {stock['week52_high']:,}원")
            lines.append(f"  - 52주 최저가: {stock['week52_low']:,}원")
            lines.append(f"  - 52주 내 위치: {stock['price_position']}%")
            if stock.get("per"):
                lines.append(f"  - PER: {stock['per']}")
            if stock.get("pbr"):
                lines.append(f"  - PBR: {stock['pbr']}")
            if stock.get("eps"):
                lines.append(f"  - EPS: {stock['eps']}")
            if stock.get("roe"):
                lines.append(f"  - ROE: {stock['roe']}%")
            if stock.get("operating_margin"):
                lines.append(f"  - 영업이익률: {stock['operating_margin']}%")
            if stock.get("debt_to_equity"):
                lines.append(f"  - 부채비율: {stock['debt_to_equity']}%")

    return "\n".join(lines)