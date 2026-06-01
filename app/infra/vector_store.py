import os
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

load_dotenv()

# 컨테이너 환경(Docker)이나 다른 서버로 이전할 때 코드 수정 없이 
# 데이터 저장 경로를 유연하게 주입하기 위해 환경 변수로 관리
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")


def get_client() -> chromadb.ClientAPI:
    """ChromaDB 클라이언트 반환"""

    # 인메모리(In-Memory) 방식은 서버 종료 시 데이터가 휘발되므로, 
    # 지정한 로컬 디스크 경로에 임베딩 데이터를 파일로 물리 저장하는 `PersistentClient`를 사용
    return chromadb.PersistentClient(
        path=CHROMA_PERSIST_DIR,
        # ChromaDB는 기본적으로 익명 사용 통계(Telemetry)를 수집하여 오픈소스 본사 서버로 전송합니다.
        # 내부 보안 정책 준수 및 불필요한 아웃바운드 네트워크 트래픽을 차단하기 위해 이를 비활성화(False)
        settings=Settings(anonymized_telemetry=False),  
    )


def get_news_collection() -> chromadb.Collection:
    """뉴스 저장용 컬렉션 반환"""

    client = get_client()

    # 컬렉션이 이미 존재할 때 재생성(Create)을 시도하면 에러가 납니다. 
    # `get_or_create_collection`을 사용하여 멱등성(Idempotency: 여러 번 실행해도 같은 결과 보장)을 확보
    return client.get_or_create_collection(
        name="news",
        # 벡터 간의 유사도를 측정하는 수학적 기준을 설정합니다.
        # 뉴스 분석/추천과 같은 자연어 처리(NLP) 분야
        # '방향성의 유사도'를 정확히 측정하는 코사인 유사도(Cosine Similarity)가 정석
        metadata={"hnsw:space": "cosine"},  
    )


def save_articles(articles: list[dict], embeddings: list[list[float]]) -> None:
    """뉴스 기사와 임베딩 벡터를 ChromaDB 에 저장"""

    collection = get_news_collection()

    ids = []          # 고유 식별자 리스트
    documents = []    # 시맨틱(의미적) 검색의 대상이 될 원문 텍스트
    metadatas = []    # 검색 이후 사용자에게 보여주거나 필터링(Filtering)에 사용할 메타데이터

    for article in articles:
        # 뉴스 URL은 전 세계에서 고유하므로 이를 ID로 채택합니다. 
        # 이를 통해 동일한 기사가 여러 번 수집되더라도 DB 내에 중복 데이터가 쌓이는 것을 차단
        ids.append(article["url"])
        
        # LLM 임베딩 모델이 제목과 요약문을 하나의 맥락(Context)으로 인지하여 
        # 벡터를 생성했으므로, 검색 시 매칭률을 높이기 위해 두 텍스트를 합쳐서 저장
        documents.append(f"{article['title']} {article['summary']}")
        
        # ChromaDB는 딕셔너리 내의 밸류값으로 중첩된 객체나 datetime 객체를 받지 못 함
        # 데이터 정규화를 위해 날짜 데이터를 문자열(`str()`)로 강제 치환
        metadatas.append({
            "title": article["title"],
            "url": article["url"],
            "source": article["source"],
            "published_at": str(article["published_at"]),
        })

    # 일반적인 `insert`를 쓰면 이미 존재하는 URL(ID)일 때 중복 키 에러가 발생합니다.
    # `upsert`를 사용하여 뉴스 내용이 수정되었거나 재수집되었을 때 에러 없이 자연스럽게 '덮어쓰기(수정)' 되도록 처리
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

    # 질문(Query)을 임베딩한 벡터를 전달하여 고차원 벡터 공간에서 가장 가까운 거리에 있는 고유 뉴스들을 찾아냅니다.
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results, # 분석에 활용할 핵심 뉴스 상위 N개 추출
    )

    articles = []
    # ChromaDB의 리턴값 구조는 결과 행렬이 3차원 리스트 형태
    # 서비스 레이어(비즈니스 로직)에서 쉽게 접근하고 가독성을 높일 수 있도록 깔끔한 딕셔너리 구조로 재가공(Mapping)
    for i, metadata in enumerate(results["metadatas"][0]):
        articles.append({
            **metadata,
            # 코사인 거리는 0에 가까울수록 두 벡터가 '같다(유사하다)'는 의미
            # 정렬 및 필터링의 척도로 삼기 위해 거리 값을 함께 포함하여 반환
            "distance": results["distances"][0][i],  
        })

    return articles