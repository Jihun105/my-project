import os

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# .env 파일에서 환경변수 불러오기
load_dotenv()

# 사용할 임베딩 모델 (.env 의 EMBEDDING_MODEL)
# jhgan/ko-sroberta-multitask = 한국어 특화 임베딩 모델
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "jhgan/ko-sroberta-multitask")

# 모델을 전역 변수로 한 번만 로드
# 매번 로드하면 느려서 서버 시작할 때 한 번만 로드해요
_model = None


def get_model() -> SentenceTransformer:
    """임베딩 모델 반환 (최초 1회만 로드)"""
    global _model

    if _model is None:
        print(f"임베딩 모델 로드 중: {EMBEDDING_MODEL}")
        _model = SentenceTransformer(EMBEDDING_MODEL)
        print("임베딩 모델 로드 완료")

    return _model


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """텍스트 리스트를 벡터 리스트로 변환"""
    import asyncio

    model = get_model()

    # SentenceTransformer 는 동기 함수라서
    # asyncio 의 스레드풀에서 실행해서 비동기처럼 동작하게 함
    loop = asyncio.get_event_loop()
    embeddings = await loop.run_in_executor(
        None,                          # 기본 스레드풀 사용
        lambda: model.encode(          # 실행할 동기 함수
            texts,
            show_progress_bar=True,    # 진행률 표시
            batch_size=32,             # 한 번에 32개씩 처리
        )
    )

    # numpy array → list 로 변환 (ChromaDB 저장을 위해)
    return embeddings.tolist()


async def embed_articles(articles: list[dict]) -> list[list[float]]:
    """뉴스 기사 리스트를 벡터 리스트로 변환"""

    # 제목 + 요약을 합쳐서 임베딩
    # 제목만 쓰면 정보가 부족하고, 본문 전체는 너무 길어서
    texts = [
        f"{article['title']} {article['summary']}"
        for article in articles
    ]

    return await embed_texts(texts)