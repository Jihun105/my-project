from contextlib import asynccontextmanager
# lifespan을 만들기 위해 필요한 도구

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.app_router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버가 켜지고 꺼질 때 뭘 할지 정의하는 함수
    # 서버 시작 시 실행
    print("서버 시작")
    yield
    # 서버 종료 시 실행
    print("서버 종료")


app = FastAPI(
    title="뉴스 트렌드 분석 & 투자 가이드",
    description="RSS 뉴스 수집 → 트렌드 분석 → 투자 가이드 생성 API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    # 프론트엔드(예: React, Vue, Next.js 등)가 다른 도메인(또는 포트)에서 이 API를 호출할 수 있도록 허용
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)