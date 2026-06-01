import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

# 서비스 환경에 따라 가볍고 빠른 모델(예: ko-MiniLM)이나 
# 정확도가 높은 대형 모델로 유연하게 교체할 수 있도록 환경 변수화했습니다.
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "jhgan/ko-sroberta-multitask")

# ==========================================
# 싱글톤 패턴(Singleton Pattern)을 위한 전역 변수
# ==========================================
# 인공지능(AI) 모델 파일은 크기가 수백 MB에서 수 GB에 달하며, 메모리에 올리는(Load) 데만 수 초가 걸립니다.
# 요청이 들어올 때마다 모델을 새로 로드하면 서버가 멈추거나 메모리 초과(OOM)로 서버가 다운
# 따라서 전역 변수를 활용해 메모리에 딱 한 번만 올리고 공유하는 방식
_model = None


def get_model() -> SentenceTransformer:
    """임베딩 모델 반환 (최초 1회만 로드하는 Lazy Initialization)"""
    global _model

    if _model is None:
        print(f"임베딩 모델 로드 중: {EMBEDDING_MODEL}")
        # ◀ 실제로 사용되는 시점(최초 호출)에만 모델을 메모리에 로드하여 서버 시작 속도를 최적화
        _model = SentenceTransformer(EMBEDDING_MODEL)
        print("임베딩 모델 로드 완료")

    return _model


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """텍스트 리스트를 벡터 리스트로 변환"""
    import asyncio

    model = get_model()

    # ==========================================
    # 비동기 스레드 오프로딩 (Thread Offloading)
    # ==========================================
    # SentenceTransformer의 `model.encode()`는 GPU/CPU의 연산 자원을 100% 끄집어 쓰는 '동기식 CPU-Bound 연산'
    # 이를 일반적인 async 함수 내부에서 그냥 실행해 버리면 연산이 끝날 때까지 FastAPI의 싱글 스레드가 완전히 얼어붙어(Blocking),
    # 다른 유저들의 가벼운 API 요청(예: /health)조차 처리하지 못하고 먹통
    loop = asyncio.get_event_loop()
    
    # `run_in_executor`를 사용하여 이 무거운 연산 작업을 백그라운드 스레드풀로 격리(Offload)
    # 메인 이벤트 루프는 자유롭게 다른 유저의 웹 요청을 처리하고, 임베딩 연산은 별도 스레드에서 안전하게 수행
    embeddings = await loop.run_in_executor(
        None,                          # 기본 ThreadPoolExecutor 사용
        lambda: model.encode(          # 스레드풀에서 실행할 타겟 함수
            texts,
            show_progress_bar=True,    # 대량 데이터 처리 시 백엔드 로그를 통해 진행 상황 모니터링 가능
            # 수천 개의 문장을 한 번에 GPU/CPU에 밀어 넣으면 메모리가 터집니다. 
            # 32개씩 쪼개서 순차 연산(Batching)함으로써 메모리 안정성을 확보합니다.
            batch_size=32,             
        )
    )

    # `model.encode` 결과물은 고성능 연산용 'NumPy Array'입니다.
    # 하지만 앞서 작성한 ChromaDB나 FastAPI의 JSON 응답은 파이썬 순정 데이터 타입만 호환되므로 `.tolist()`로 변환(Type Casting)합니다.
    return embeddings.tolist()


async def embed_articles(articles: list[dict]) -> list[list[float]]:
    """뉴스 기사 리스트를 벡터 리스트로 변환"""

    # ==========================================
    # 시맨틱 컨텍스트 결합 (Context Merging)
    # ==========================================
    # 임베딩 모델은 맥락이 풍부할수록 두 문장의 의미가 비슷한지 더 잘 찾아냅니다.
    # '제목'만 쓰면 너무 짧아서 키워드가 누락되고, '본문 전체'를 다 쓰면 모델이 수용할 수 있는 최대 글자 수(Token Limit)를 초과하여 
    # 뒷부분이 잘려 나가거나 노이즈가 섞입니다. 
    # '제목 + 요약문' 조합은 핵심 맥락(Context)만 압축하여 검색 정확도를 극대화하는 가장 이상적인 전략입니다.
    texts = [
        f"{article['title']} {article['summary']}"
        for article in articles
    ]

    return await embed_texts(texts)