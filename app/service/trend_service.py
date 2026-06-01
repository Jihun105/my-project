import os
from collections import Counter

import numpy as np
from dotenv import load_dotenv
from kiwipiepy import Kiwi
from sklearn.cluster import KMeans

from infra.vector_store import get_news_collection

load_dotenv()

# Kiwi = 한국어 형태소 분석기
# 형태소 분석 = 문장을 의미 있는 단위로 쪼개는 것
# ex) "삼성전자 주가 상승" → ["삼성전자", "주가", "상승"]
kiwi = Kiwi()

# 섹터 키워드 사전
# 뉴스에 이 키워드가 많이 나오면 해당 섹터로 분류
SECTOR_KEYWORDS = {
    "반도체": ["반도체", "메모리", "파운드리", "삼성전자", "SK하이닉스", "TSMC"],
    "2차전지": ["배터리", "2차전지", "전기차", "리튬", "LG에너지솔루션", "삼성SDI"],
    "금융": ["금리", "은행", "증권", "보험", "대출", "금융"],
    "바이오": ["바이오", "제약", "임상", "신약", "의료"],
    "부동산": ["부동산", "아파트", "분양", "전세", "임대"],
    "에너지": ["에너지", "원유", "가스", "태양광", "풍력"],
    "IT": ["AI", "인공지능", "소프트웨어", "플랫폼", "클라우드"],
}
# 불용어 목록 (의미 없는 단어들)
STOPWORDS = {
    "연합뉴스", "기자", "서울", "뉴스", "미디어", "헤럴드",
    "매일경제", "한국경제", "파이낸셜", "제공", "저작권",
    "무단", "전재", "재배포", "금지", "사진", "출처",
}

def extract_keywords(text: str, top_n: int = 5) -> list[str]:
    """텍스트에서 명사 키워드 추출"""

    # Kiwi 로 형태소 분석
    result = kiwi.analyze(text)

    # 명사(NNG: 일반명사, NNP: 고유명사)만 추출
    nouns = [
        token.form for token in result[0][0]
        if token.tag in ("NNG", "NNP")
        and len(token.form) > 1
        and token.form not in STOPWORDS  # 불용어 제외
    ]

    # 가장 많이 나온 명사 top_n 개 반환
    counter = Counter(nouns)
    return [word for word, _ in counter.most_common(top_n)]


def classify_sector(keywords: list[str]) -> str:
    """키워드로 섹터 분류"""

    sector_scores = {sector: 0 for sector in SECTOR_KEYWORDS}

    for keyword in keywords:
        for sector, sector_kws in SECTOR_KEYWORDS.items():
            if keyword in sector_kws:
                sector_scores[sector] += 1

    # 가장 점수 높은 섹터 반환
    best_sector = max(sector_scores, key=sector_scores.get)

    # 점수가 0 이면 분류 불가
    if sector_scores[best_sector] == 0:
        return "기타"

    return best_sector


async def analyze_trends(n_clusters: int = None) -> dict:
    """저장된 뉴스를 클러스터링해서 트렌드 분석"""

    collection = get_news_collection()

    # ChromaDB 에서 뉴스 + 임베딩 벡터 가져오기
    results = collection.get(include=["embeddings", "metadatas", "documents"])

    if not results["ids"]:
        return {"clusters": [], "hot_sectors": []}

    # 임베딩 벡터를 numpy array 로 변환
    embeddings = np.array(results["embeddings"])
    metadatas = results["metadatas"]
    documents = results["documents"]

    # 뉴스가 클러스터 수보다 적으면 클러스터 수 조정
    # 뉴스 양에 따라 클러스터 수 동적 조정
    if n_clusters is None:
        if len(embeddings) < 20:
            n_clusters = 3
        elif len(embeddings) < 50:
            n_clusters = 5
        elif len(embeddings) < 100:
            n_clusters = 8
        else:
            n_clusters = 12

    # 뉴스가 클러스터 수보다 적으면 클러스터 수 조정
    n_clusters = min(n_clusters, len(embeddings))

    # KMeans 클러스터링
    # 비슷한 벡터끼리 묶어서 n_clusters 개의 그룹으로 나눔
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(embeddings)

    # 클러스터별로 뉴스 그룹화
    clusters = {}
    for i, label in enumerate(labels):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append({
            "metadata": metadatas[i],
            "document": documents[i],
        })

    # 클러스터별 키워드 및 섹터 분석
    cluster_results = []
    sector_counter = Counter()

    for label, articles in clusters.items():
        # 클러스터 내 모든 텍스트 합치기
        combined_text = " ".join([a["document"] for a in articles])

        # 키워드 추출
        keywords = extract_keywords(combined_text, top_n=5)

        # 섹터 분류
        sector = classify_sector(keywords)
        sector_counter[sector] += len(articles)

        cluster_results.append({
            "cluster_id": int(label),
            "news_count": len(articles),
            "top_keywords": keywords,
            "sector": sector,
            # 클러스터 대표 뉴스 제목 (첫 번째 뉴스)
            "label": articles[0]["metadata"].get("title", ""),
            # 클러스터 내 상위 10개 뉴스 제목 목록
            "top_titles": [
                a["metadata"].get("title", "")
                for a in articles[:10]
                if a["metadata"].get("title", "")
            ],
        })

    # 뉴스 많은 순으로 정렬
    cluster_results.sort(key=lambda x: x["news_count"], reverse=True)

    return {
        "clusters": cluster_results,
        # 가장 뉴스 많은 상위 3개 섹터
        "hot_sectors": [sector for sector, _ in sector_counter.most_common(3)],
    }