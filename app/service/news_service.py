import asyncio
from datetime import datetime

from infra.rss_client import fetch_all_rss
from infra.vector_store import save_articles, get_news_collection
from service.embed_service import embed_articles


async def collect_and_preprocess() -> int:
    """RSS 수집 → 임베딩 → ChromaDB 저장 한 번에 처리"""

    # 1. RSS 에서 뉴스 수집
    print("뉴스 수집 시작...")
    articles = await fetch_all_rss()

    if not articles:
        print("수집된 뉴스 없음")
        return 0

    # 2. 이미 저장된 뉴스 중복 체크
    collection = get_news_collection()
    existing_ids = set(collection.get()["ids"])

    # URL 이 이미 저장된 뉴스는 건너뜀
    new_articles = [
        article for article in articles
        if article["url"] not in existing_ids
    ]

    if not new_articles:
        print("새로운 뉴스 없음")
        return 0

    print(f"새로운 뉴스 {len(new_articles)}건 처리 시작...")

    # 3. 텍스트 임베딩 (벡터 변환)
    print("임베딩 중...")
    embeddings = await embed_articles(new_articles)

    # 4. ChromaDB 에 저장
    print("저장 중...")
    save_articles(new_articles, embeddings)

    return len(new_articles)


async def get_news_list(limit: int = 20, sector: str = None) -> list[dict]:
    """저장된 뉴스 목록 조회"""

    collection = get_news_collection()

    # ChromaDB 에서 전체 뉴스 가져오기
    results = collection.get(
        limit=limit,
        where={"sector": sector} if sector else None,
    )

    if not results["ids"]:
        return []

    # 결과를 보기 좋게 정리
    articles = []
    for i, id_ in enumerate(results["ids"]):
        articles.append({
            **results["metadatas"][i],
            "id": id_,
        })

    return articles