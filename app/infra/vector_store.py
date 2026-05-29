# rss_client에서 가져온 뉴스 -> ChromaDB 저장
# => 저장소 연결
import os

import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

# .env 파일에서 환경변수 불러오기
load_dotenv()

# ChromaDB 저장 경로 (.env 의 CHROMA_PERSIST_DIR)
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")


def get_client() -> chromadb.ClientAPI:
    """ChromaDB 클라이언트 반환"""

    # PersistentClient = 데이터를 파일로 저장하는 클라이언트
    # 서버 재시작해도 데이터 유지됨
    return chromadb.PersistentClient(
        path=CHROMA_PERSIST_DIR,
        settings=Settings(anonymized_telemetry=False),  
        # anonymized_telemetry=False (원격 분석 비활성화)
    )


def get_news_collection() -> chromadb.Collection:
    """뉴스 저장용 컬렉션 반환"""

    client = get_client()

    # get_or_create_collection = 있으면 가져오고 없으면 새로 만들기
    # 컬렉션 = RDB 의 테이블과 비슷한 개념
    return client.get_or_create_collection(
        name="news",
        metadata={"hnsw:space": "cosine"},  # 유사도 계산 방식 = 코사인 유사도
    )


def save_articles(articles: list[dict], embeddings: list[list[float]]) -> None:
    """뉴스 기사와 임베딩 벡터를 ChromaDB 에 저장"""

    collection = get_news_collection()

    # ChromaDB 에 저장할 데이터 준비
    ids = []          # 각 문서의 고유 ID
    documents = []    # 실제 텍스트 (제목 + 요약)
    metadatas = []    # 부가 정보 (출처, 날짜 등)

    for article in articles:
        # URL 을 ID 로 사용 (중복 방지)
        ids.append(article["url"])
        documents.append(f"{article['title']} {article['summary']}")
        metadatas.append({
            "title": article["title"],
            "url": article["url"],
            "source": article["source"],
            "published_at": str(article["published_at"]),
        })

    # upsert = insert + update
    # 이미 있는 ID 면 업데이트, 없으면 새로 삽입
    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    print(f"{len(ids)}건 저장 완료")


def search_similar(query_embedding: list[float], n_results: int = 10) -> list[dict]:
    """쿼리 벡터와 유사한 뉴스 검색"""

    collection = get_news_collection()

    # query = 벡터 유사도 검색
    # n_results = 상위 몇 개 반환할지
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
    )

    # 검색 결과를 보기 좋게 정리
    articles = []
    for i, metadata in enumerate(results["metadatas"][0]):
        articles.append({
            **metadata,
            "distance": results["distances"][0][i],  # 유사도 거리 (낮을수록 유사)
        })

    return articles