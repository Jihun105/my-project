import asyncio
from datetime import datetime

import yfinance as yf
import FinanceDataReader as fdr

# 전체 종목 목록 캐시 (서버 시작 시 한 번만 로드)
_ticker_cache: dict[str, str] = {}


def _build_ticker_cache() -> dict[str, str]:
    """FinanceDataReader로 전체 상장 종목 목록 로드 (종목명 → 티커)"""
    print("종목 목록 로드 중...")
    cache = {}

    try:
        # 코스피 종목 목록
        kospi = fdr.StockListing("KOSPI")
        for _, row in kospi.iterrows():
            name = row["Name"]
            code = str(row["Code"]).zfill(6)  # 6자리로 맞추기
            cache[name] = f"{code}.KS"

        # 코스닥 종목 목록
        kosdaq = fdr.StockListing("KOSDAQ")
        for _, row in kosdaq.iterrows():
            name = row["Name"]
            code = str(row["Code"]).zfill(6)
            cache[name] = f"{code}.KQ"

        print(f"종목 목록 로드 완료: {len(cache)}개")
    except Exception as e:
        print(f"종목 목록 로드 실패: {e}")

    return cache


def get_ticker_cache() -> dict[str, str]:
    """종목 캐시 반환 (없으면 생성)"""
    global _ticker_cache
    if not _ticker_cache:
        _ticker_cache = _build_ticker_cache()
    return _ticker_cache


def find_ticker(company_name: str) -> str | None:
    """종목명으로 야후 파이낸스 티커 검색"""
    cache = get_ticker_cache()

    # 정확히 일치하는 종목명 검색
    if company_name in cache:
        return cache[company_name]

    # 부분 일치 검색 (예: "삼성" → "삼성전자", "삼성SDI" 등)
    matches = [
        (name, ticker)
        for name, ticker in cache.items()
        if company_name in name
    ]

    if matches:
        # 가장 짧은 이름 반환 (가장 정확한 매칭)
        return min(matches, key=lambda x: len(x[0]))[1]

    return None


async def get_stock_data(company_name: str) -> dict | None:
    """종목명으로 주가 및 재무 데이터 가져오기"""

    ticker_symbol = find_ticker(company_name)
    if not ticker_symbol:
        print(f"종목 없음: {company_name}")
        return None

    loop = asyncio.get_event_loop()

    data = await loop.run_in_executor(
        None,
        lambda: _fetch_stock_data(ticker_symbol, company_name)
    )

    return data


def _fetch_stock_data(ticker_symbol: str, company_name: str) -> dict | None:
    """yfinance 로 주가 및 재무 데이터 가져오기 (동기)"""

    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        hist = ticker.history(period="1y")

        if hist.empty:
            return None

        current_price = hist["Close"].iloc[-1]
        week52_high = hist["Close"].max()
        week52_low = hist["Close"].min()

        price_position = (
            (current_price - week52_low) / (week52_high - week52_low) * 100
            if week52_high != week52_low else 50
        )

        if len(hist) >= 2:
            prev_price = hist["Close"].iloc[-2]
            change_pct = (current_price - prev_price) / prev_price * 100
        else:
            change_pct = 0

        return {
            "name": company_name,
            "ticker": ticker_symbol,
            # 현재가 & 등락률
            "current_price": int(round(current_price)),
            "change_pct": float(round(change_pct, 2)),
            # 52주 데이터
            "week52_high": int(round(week52_high)),
            "week52_low": int(round(week52_low)),
            "price_position": float(round(price_position, 1)),
            # 밸류에이션
            "per": float(round(info.get("trailingPE"), 2)) if info.get("trailingPE") else None,
            "pbr": float(round(info.get("priceToBook"), 2)) if info.get("priceToBook") else None,
            "eps": float(round(info.get("trailingEps"), 2)) if info.get("trailingEps") else None,
            # 수익성
            "roe": float(round(info.get("returnOnEquity") * 100, 2)) if info.get("returnOnEquity") else None,
            "operating_margin": float(round(info.get("operatingMargins") * 100, 2)) if info.get("operatingMargins") else None,
            # 안정성
            "debt_to_equity": float(round(info.get("debtToEquity"), 2)) if info.get("debtToEquity") else None,
            # 기타
            "market_cap": int(info.get("marketCap")) if info.get("marketCap") else None,
            "volume": int(info.get("volume")) if info.get("volume") else None,
        }
    except Exception as e:
        print(f"주가 데이터 오류 ({company_name}): {e}")
        return None


async def get_multiple_stocks(company_names: list[str]) -> list[dict]:
    """여러 종목 데이터 동시에 가져오기"""

    tasks = [get_stock_data(name) for name in company_names]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    stocks = []
    for result in results:
        if isinstance(result, Exception) or result is None:
            continue
        stocks.append(result)

    return stocks