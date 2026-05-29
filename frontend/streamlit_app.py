import httpx
import streamlit as st

# 백엔드 API 주소
API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="뉴스 트렌드 투자 가이드",
    page_icon="📈",
    layout="wide",
)

st.title("📈 뉴스 트렌드 분석 & 투자 가이드")
st.caption("RSS 뉴스 수집 → 트렌드 분석 → AI 투자 가이드 생성")

st.divider()

# ── 사이드바 ──────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 설정")

    st.subheader("뉴스 수집")
    if st.button("🔄 뉴스 수집 실행", use_container_width=True):
        with st.spinner("뉴스 수집 중..."):
            try:
                response = httpx.post(f"{API_URL}/news/collect")
                data = response.json()
                st.success(data["message"])
            except Exception as e:
                st.error(f"오류: {e}")

    st.divider()

    st.subheader("투자 가이드")
    if st.button("🤖 전체 파이프라인 실행", use_container_width=True):
        with st.spinner("분석 중... (30초 ~ 1분 소요)"):
            try:
                response = httpx.post(
                    f"{API_URL}/invest/run-pipeline",
                    timeout=120,
                )
                data = response.json()
                # 결과를 세션 상태에 저장
                st.session_state["pipeline_result"] = data["result"]
                st.success("완료!")
            except Exception as e:
                st.error(f"오류: {e}")

# ── 메인 화면 ──────────────────────────────────────
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📰 수집된 뉴스")
    try:
        response = httpx.get(f"{API_URL}/news/list?limit=20")
        news_data = response.json()

        if news_data["total"] == 0:
            st.info("수집된 뉴스가 없어요. 사이드바에서 뉴스 수집을 실행해줘요.")
        else:
            st.caption(f"총 {news_data['total']}건")
            for item in news_data["items"]:
                with st.expander(item.get("title", "제목 없음")):
                    st.write(f"**출처:** {item.get('source', '')}")
                    st.write(f"**날짜:** {item.get('published_at', '')}")
                    st.link_button("기사 보기", item.get("url", "#"))
    except Exception as e:
        st.error(f"뉴스 목록 불러오기 실패: {e}")

with col2:
    st.subheader("📊 투자 가이드")

    # 파이프라인 실행 결과가 있으면 표시
    if "pipeline_result" in st.session_state:
        result = st.session_state["pipeline_result"]
        report = result.get("report", {})

        st.caption(f"생성 시각: {report.get('generated_at', '')}")
        st.markdown(report.get("report", ""))

        # 트렌드 데이터 시각화
        trend_data = report.get("trend_data", {})
        if trend_data.get("clusters"):
            st.divider()
            st.subheader("🔥 섹터별 뉴스 분포")

            import plotly.express as px
            import pandas as pd

            df = pd.DataFrame(trend_data["clusters"])
            fig = px.bar(
                df,
                x="sector",
                y="news_count",
                color="sector",
                title="섹터별 뉴스 수",
                labels={"sector": "섹터", "news_count": "뉴스 수"},
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("사이드바에서 전체 파이프라인을 실행해줘요.")