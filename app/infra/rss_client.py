import feedparser
import httpx
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

# 하드코딩을 피하고 운영 환경(Prod)과 개발 환경(Dev)에 따라 수집 대상과 기간을 유연하게 바꾸기 위함
RSS_URLS = os.getenv("RSS_URLS", "").split(",")
NEWS_DAYS = int(os.getenv("NEWS_DAYS", "7"))

"""# feedparser가 변환한 후의 `entry` 객체 내부 형태 (실제 구조)
entry = {
    "title": "2026년 AI 반도체 투자 트렌드 분석",
    "link": "https://news.example.com/articles/123",
    "summary": "올해 주식 시장을 이끌어갈 반도체 대장주는...",
    "published": "Mon, 01 Jun 2026 09:00:00 +0900",
    
    # "published_parsed": time.struct_time(tm_year=2026, tm_mon=6, tm_mday=1, tm_hour=9, tm_min=0, tm_sec=0, tm_wday=0, tm_yday=152, tm_isdst=0)
}"""

async def fetch_rss(url: str) -> list[dict]:
    """단일 RSS URL에서 뉴스 가져오기"""
    # 외부 서버와 통신하는 I/O 작업 동안 다른 작업(예: 대화형 API 요청)이 멈추지 않도록 비동기 클라이언트를 사용
    # context manager(`async with`)를 사용하여 HTTP 연결(Connection)을 풀링하고, 작업 완료 후 포트를 안전하게 닫아 누수를 방지
    async with httpx.AsyncClient() as client:
        # 외부 RSS 서버가 응답이 없거나 느릴 때 시스템 전체가 무한대기(Hang) 상태에 빠지는 것을 막기 위해 10초 타임아웃을 강제
        response = await client.get(url, timeout=10)
        
        # 피드파서는 구조화된 XML 문서를 파이썬 딕셔너리 형태로 쉽게 다룰 수 있게 추상화해 주는 표준적인 도구
        feed = feedparser.parse(response.text)

    # 오래된 데이터까지 전부 분석하면 LLM 비용이 낭비되고 분석 효율이 떨어지므로, 최근 N일 이내의 데이터만 필터링(Data Pruning)하기 위한 기준점을 계산
    cutoff = datetime.now() - timedelta(days=NEWS_DAYS)
    articles = []


    for entry in feed.entries:
        # RSS 제공처마다 날짜 포맷이 다르거나 필드가 누락될 수 있으므로 `get`으로 접근하여 Key Error를 방지합니다.
        published = entry.get("published_parsed")
        if published:
            # feedparser가 주는 구조화된 튜플(*struct_time) 데이터 중 앞 6개(년, 월, 일, 시, 분, 초)를 추출해 datetime 객체로 변환
            published_dt = datetime(*published[:6])
            
            # 가동 시간 효율화를 위해 기준일(cutoff)보다 과거 뉴스는 메모리에 올리지 않고 즉시 제외(Early Skip)합니다.
            if published_dt < cutoff:
                continue

        # 원본 RSS 데이터의 규격이 제각각이므로, 우리 서비스 내에서 일관되게 다룰 수 있도록 '정규화(Normalization)'된 딕셔너리 구조로 재조립합니다.
        articles.append({
            "title": entry.get("title", ""),
            "url": entry.get("link", ""),
            "summary": entry.get("summary", ""),
            "source": feed.feed.get("title", url), # 출처명 누락 시 안전장치로 요청 URL 사용
            "published_at": published_dt if published else datetime.now(),
        })

    return articles


async def fetch_all_rss() -> list[dict]:
    """모든 RSS 소스에서 뉴스 가져오기"""
    import asyncio

    # ==========================================
    # 동시성 처리 (Concurrency) & 병렬 요청
    # ==========================================
    # 10개의 RSS 주소가 있을 때 순차적으로 가져오면 총 10~20초가 걸리지만, 
    # `asyncio.gather`를 통해 동시에(Concurrent) 요청하면 가장 느린 서버의 응답 시간(예: 1~2초) 안에 모든 수집이 완료
    tasks = [fetch_rss(url.strip()) for url in RSS_URLS if url.strip()]
    
    # `return_exceptions=True`는 10개 중 1개의 RSS 서버가 에러가 나더라도 
    # 전체 프로세스가 폭발하지 않고 나머지 9개 서버의 데이터는 무사히 수집되도록 예외를 격리(Fault Tolerance)
    results = await asyncio.gather(*tasks, return_exceptions=True)

    articles = []
    for result in results:
        # 에러가 발생한 태스크는 Exception 객체로 들어오므로, 로그만 남기고 정상 데이터만 수집
        if isinstance(result, Exception):
            print(f"RSS 수집 오류: {result}")
            continue
        articles.extend(result)

    # ==========================================
    # 중복 데이터 제거 (Data Deduplication)
    # ==========================================
    # 여러 RSS 매체에서 같은 뉴스를 송출하거나 중복 수집된 경우, 
    # 데이터 신뢰성을 지키고 불필요한 중복 가공비용(LLM 토큰비 등)을 아끼기 위해 URL을 고유 키(Set)로 활용해 필터링합니다.
    seen = set()
    unique = []
    for article in articles:
        if article["url"] not in seen:
            seen.add(article["url"])
            unique.append(article)

    print(f"총 {len(unique)}건 뉴스 수집 완료")
    return unique