# RSS에서 뉴스 가져오기 
import feedparser
import httpx
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

RSS_URLS = os.getenv("RSS_URLS", "").split(",")
NEWS_DAYS = int(os.getenv("NEWS_DAYS", "7"))


async def fetch_rss(url: str) -> list[dict]:
    """단일 RSS URL에서 뉴스 가져오기"""
    async with httpx.AsyncClient() as client:
        # httpx.AsyncClient로 비동기 HTTP 요청
        # with : 자동으로 연결 종료
        response = await client.get(url, timeout=10)
        # feedparser 가 RSS XML 을 파싱해서 딕셔너리로 변환
        feed = feedparser.parse(response.text)

    # 오늘 기준 N일 전 날짜 계산 (이보다 오래된 뉴스는 스킵)
    cutoff = datetime.now() - timedelta(days=NEWS_DAYS)
    articles = []

    for entry in feed.entries:
        # RSS 발행일 파싱 (없는 경우도 있어서 .get 으로 안전하게)
        published = entry.get("published_parsed")
        if published:
            published_dt = datetime(*published[:6])
            # 날짜 데이터를 datetime 객체로 만듬
            if published_dt < cutoff:
                continue

        articles.append({
            "title": entry.get("title", ""),
            "url": entry.get("link", ""),
            "summary": entry.get("summary", ""),
            "source": feed.feed.get("title", url),
            "published_at": published_dt if published else datetime.now(),
        })

    return articles


async def fetch_all_rss() -> list[dict]:
    """모든 RSS 소스에서 뉴스 가져오기"""
    import asyncio

    tasks = [fetch_rss(url.strip()) for url in RSS_URLS if url.strip()]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    articles = []
    for result in results:
        if isinstance(result, Exception):
            print(f"RSS 수집 오류: {result}")
            continue
        articles.extend(result)

    # 중복 URL 제거
    seen = set()
    unique = []
    for article in articles:
        if article["url"] not in seen:
            seen.add(article["url"])
            unique.append(article)

    print(f"총 {len(unique)}건 뉴스 수집 완료")
    return unique