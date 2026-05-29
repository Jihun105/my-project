from typing import TypedDict

from langgraph.graph import StateGraph, END

from service.news_service import collect_and_preprocess
from service.trend_service import analyze_trends
from service.invest_service import generate_invest_report


# 파이프라인 전체에서 공유되는 상태
# 각 노드가 이 상태를 읽고 업데이트해요
class AgentState(TypedDict):
    # 수집된 뉴스 수
    news_count: int
    # 트렌드 분석 결과
    trend_data: dict
    # 투자 가이드 리포트
    report: dict
    # 에러 메시지 (에러 없으면 None)
    error: str | None


# ── 노드 함수들 ──────────────────────────────────────
# 각 노드는 현재 상태를 받아서 업데이트된 상태를 반환해요

async def node_collect_news(state: AgentState) -> AgentState:
    """노드 1: 뉴스 수집 → 임베딩 → ChromaDB 저장"""
    print("\n[1/3] 뉴스 수집 중...")
    try:
        count = await collect_and_preprocess()
        return {**state, "news_count": count, "error": None}
    except Exception as e:
        return {**state, "error": f"뉴스 수집 실패: {e}"}


async def node_analyze_trends(state: AgentState) -> AgentState:
    """노드 2: 트렌드 분석"""
    print("\n[2/3] 트렌드 분석 중...")
    try:
        trend_data = await analyze_trends()
        return {**state, "trend_data": trend_data, "error": None}
    except Exception as e:
        return {**state, "error": f"트렌드 분석 실패: {e}"}


async def node_generate_report(state: AgentState) -> AgentState:
    """노드 3: 투자 가이드 생성"""
    print("\n[3/3] 투자 가이드 생성 중...")
    try:
        report = await generate_invest_report()
        return {**state, "report": report, "error": None}
    except Exception as e:
        return {**state, "error": f"리포트 생성 실패: {e}"}


# ── 조건부 엣지 ──────────────────────────────────────
# 에러가 있으면 파이프라인 중단, 없으면 다음 노드로

def should_continue(state: AgentState) -> str:
    """에러 있으면 END, 없으면 다음 노드로"""
    if state.get("error"):
        print(f"\n파이프라인 중단: {state['error']}")
        return "end"
    return "continue"


# ── 그래프 구성 ──────────────────────────────────────

def build_graph() -> StateGraph:
    """LangGraph 파이프라인 그래프 구성"""

    graph = StateGraph(AgentState)

    # 노드 등록
    graph.add_node("collect_news", node_collect_news)
    graph.add_node("analyze_trends", node_analyze_trends)
    graph.add_node("generate_report", node_generate_report)

    # 시작 노드 설정
    graph.set_entry_point("collect_news")

    # 엣지 연결 (조건부)
    # collect_news 끝나면 → 에러 없으면 analyze_trends, 있으면 END
    graph.add_conditional_edges(
        "collect_news",
        should_continue,
        {"continue": "analyze_trends", "end": END},
    )
    graph.add_conditional_edges(
        "analyze_trends",
        should_continue,
        {"continue": "generate_report", "end": END},
    )

    # generate_report 끝나면 무조건 END
    graph.add_edge("generate_report", END)

    return graph.compile()


# 그래프 인스턴스 (한 번만 생성)
_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


async def run_agent(stream: bool = False):
    """파이프라인 실행 (스트리밍)"""

    graph = get_graph()

    initial_state = AgentState(
        news_count=0,
        trend_data={},
        report={},
        error=None,
    )

    async for chunk in graph.astream(initial_state):
        if stream:
            yield chunk


async def run_agent_once() -> dict:
    """파이프라인 실행 (단일 결과 반환)"""

    graph = get_graph()

    initial_state = AgentState(
        news_count=0,
        trend_data={},
        report={},
        error=None,
    )

    result = await graph.ainvoke(initial_state)
    return result