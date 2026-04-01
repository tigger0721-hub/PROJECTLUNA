from __future__ import annotations

import asyncio
import ast
import json
import logging
import os
import re
import time
import unicodedata
from datetime import date, datetime, timedelta, timezone
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

app = FastAPI(title="Luna Stock Chart Tutor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STOOQ_URL = "https://stooq.com/q/d/l/"
YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/"
NAVER_KR_CHART_URL = "https://fchart.stock.naver.com/siseJson.nhn"
KIS_BASE_URL = os.getenv("KIS_BASE_URL", "https://openapi.koreainvestment.com:9443").rstrip("/")
logger = logging.getLogger(__name__)
REALTIME_QUOTE_MAX_AGE_SECONDS = 5.0
_KIS_TOKEN_CACHE: Dict[str, Any] = {"access_token": None, "expires_at": 0.0}

STYLE_GUIDE = {
    "conservative": {
        "label": "보수형",
        "description": "신규 진입보다 확인과 방어를 우선하고, 손실 회피와 짧은 손절을 선호한다."
    },
    "pullback": {
        "label": "눌림매수형",
        "description": "급등 추격보다 지지선, 전고점, 이평선 눌림 이후 반등 확인을 선호한다."
    },
    "trend": {
        "label": "추세매수형",
        "description": "돌파 후 안착과 거래량 동반 여부를 중시하며 강한 종목 추종을 선호한다."
    },
    "swing": {
        "label": "단기 스윙형",
        "description": "짧은 목표와 빠른 익절·손절을 선호하며 구간 매매에 익숙하다."
    },
    "protect_profit": {
        "label": "수익보호형",
        "description": "신규 진입보다 기존 수익 보호를 우선하고, 이익 반납을 매우 싫어한다."
    },
    "trend_partial": {
        "label": "추세추종+분할익절형",
        "description": "잘 가는 종목을 따라가되 전량 홀딩보다 부분 익절과 추세 추종을 같이 선호한다."
    },
}


def normalize_ticker(ticker: str) -> str:
    return ticker.strip().lower()


US_INSTRUMENT_CATALOG: List[Dict[str, str]] = [
    {
        "symbol": "NVDA",
        "name_ko": "엔비디아",
        "name_en": "NVIDIA",
        "market": "US",
        "country": "US",
        "provider": "kis",
        "provider_symbol": "NVDA",
        "aliases": "nvidia,엔비디아,nvda",
    },
    {
        "symbol": "TSLA",
        "name_ko": "테슬라",
        "name_en": "Tesla",
        "market": "US",
        "country": "US",
        "provider": "kis",
        "provider_symbol": "TSLA",
        "aliases": "tesla,테슬라,tsla",
    },
    {
        "symbol": "AAPL",
        "name_ko": "애플",
        "name_en": "Apple",
        "market": "US",
        "country": "US",
        "provider": "kis",
        "provider_symbol": "AAPL",
        "aliases": "apple,애플,aapl",
    },
    {
        "symbol": "MSFT",
        "name_ko": "마이크로소프트",
        "name_en": "Microsoft",
        "market": "US",
        "country": "US",
        "provider": "kis",
        "provider_symbol": "MSFT",
        "aliases": "microsoft,마이크로소프트,msft",
    },
]

KR_INSTRUMENT_FILE = Path(__file__).resolve().parent.parent / "data" / "kr_instruments.json"


def _normalize_query_text(query: str) -> str:
    normalized = unicodedata.normalize("NFKC", query).strip().lower()
    return re.sub(r"\s+", " ", normalized)


def _load_kr_instrument_catalog() -> List[Dict[str, str]]:
    try:
        with KR_INSTRUMENT_FILE.open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception as e:
        logger.warning("Failed to load KR instrument file %s: %s", KR_INSTRUMENT_FILE, e)
        return []
    if not isinstance(payload, list):
        logger.warning("KR instrument file has invalid shape: expected list")
        return []
    catalog: List[Dict[str, str]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        symbol = str(item.get("symbol", "")).strip()
        name_ko = str(item.get("name_ko", "")).strip()
        if not symbol or not name_ko:
            continue
        catalog.append(
            {
                "symbol": symbol.zfill(6),
                "name_ko": name_ko,
                "name_en": str(item.get("name_en", "")).strip(),
                "market": str(item.get("market", "KRX")).strip() or "KRX",
                "country": "KR",
                "provider": "naver",
                "provider_symbol": symbol.zfill(6),
                "aliases": str(item.get("aliases", "")).strip(),
            }
        )
    return catalog


KR_INSTRUMENT_CATALOG = _load_kr_instrument_catalog()
INSTRUMENT_CATALOG = [*US_INSTRUMENT_CATALOG, *KR_INSTRUMENT_CATALOG]


def _build_catalog_index(catalog: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    index: Dict[str, Dict[str, str]] = {}
    for instrument in catalog:
        tokens = {
            instrument["symbol"].lower(),
            instrument["name_ko"].lower(),
            instrument["name_en"].lower(),
            *[token.strip().lower() for token in instrument.get("aliases", "").split(",") if token.strip()],
        }
        for token in tokens:
            index[_normalize_query_text(token)] = instrument
    return index


INSTRUMENT_INDEX = _build_catalog_index(INSTRUMENT_CATALOG)


def _resolve_us_instrument(query: str) -> Dict[str, str]:
    symbol = query.upper()
    normalized_symbol = symbol.replace(".US", "").replace(".KS", "").replace(".KQ", "")
    if not re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,9}", normalized_symbol):
        raise ValueError("입력한 종목을 찾지 못했어. 종목명이나 티커를 다시 확인해줘.")
    return {
        "symbol": normalized_symbol,
        "display_name": normalized_symbol,
        "market": "US",
        "country": "US",
        "provider": "kis",
        "provider_symbol": normalized_symbol,
        "query": query,
    }


def _resolve_kr_instrument_from_code(code: str) -> Dict[str, str]:
    normalized_code = code.zfill(6)
    catalog_hit = INSTRUMENT_INDEX.get(normalized_code)
    if catalog_hit:
        return {
            "symbol": catalog_hit["symbol"],
            "display_name": catalog_hit["name_ko"],
            "market": catalog_hit["market"],
            "country": "KR",
            "provider": "naver",
            "provider_symbol": catalog_hit["provider_symbol"],
            "query": code,
        }
    return {
        "symbol": normalized_code,
        "display_name": normalized_code,
        "market": "KRX",
        "country": "KR",
        "provider": "naver",
        "provider_symbol": normalized_code,
        "query": code,
    }


def resolve_instrument(query: str) -> Dict[str, str]:
    normalized = _normalize_query_text(query)
    if not normalized:
        raise ValueError("입력한 종목을 찾지 못했어. 종목명이나 티커를 다시 확인해줘.")

    catalog_hit = INSTRUMENT_INDEX.get(normalized)
    if catalog_hit:
        return {
            "symbol": catalog_hit["symbol"],
            "display_name": catalog_hit["name_ko"] or catalog_hit["name_en"],
            "market": catalog_hit["market"],
            "country": catalog_hit["country"],
            "provider": catalog_hit["provider"],
            "provider_symbol": catalog_hit["provider_symbol"],
            "query": query,
        }

    if re.fullmatch(r"\d{5,6}", normalized):
        return _resolve_kr_instrument_from_code(normalized)

    if re.search(r"[가-힣]", normalized):
        raise ValueError("입력한 국내 종목을 찾지 못했어. 종목명이나 종목코드를 다시 확인해줘.")

    return _resolve_us_instrument(normalized)


async def fetch_daily_prices(ticker: str) -> List[Dict[str, Any]]:
    symbol = normalize_ticker(ticker)
    params = {"s": symbol, "i": "d"}

    text = ""
    last_error: Optional[Exception] = None
    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                response = await client.get(STOOQ_URL, params=params)
                response.raise_for_status()
            text = response.text.strip()
            if text:
                break
        except httpx.ProxyError as e:
            last_error = e
            try:
                async with httpx.AsyncClient(timeout=20.0, follow_redirects=True, trust_env=False) as client:
                    response = await client.get(STOOQ_URL, params=params)
                    response.raise_for_status()
                text = response.text.strip()
                if text:
                    break
            except Exception as bypass_error:
                last_error = bypass_error
        except Exception as e:
            last_error = e
            if attempt == 0:
                await asyncio.sleep(0.25)

    if not text and last_error:
        raise ValueError(f"시세 요청이 불안정해. 잠깐 뒤에 다시 시도해줘: {last_error}")

    if not text or "No data" in text:
        raise ValueError(f"데이터를 찾지 못했어: {ticker}")

    df = pd.read_csv(StringIO(text))
    required_cols = {"Date", "Open", "High", "Low", "Close", "Volume"}
    if not required_cols.issubset(df.columns):
        raise ValueError("시세 데이터 형식이 예상과 달라")

    df = df.dropna().copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date")

    return [
        {
            "time": row["Date"].strftime("%Y-%m-%d"),
            "open": float(row["Open"]),
            "high": float(row["High"]),
            "low": float(row["Low"]),
            "close": float(row["Close"]),
            "volume": float(row["Volume"]),
        }
        for _, row in df.tail(240).iterrows()
    ]


async def fetch_yahoo_daily_prices(provider_symbol: str) -> List[Dict[str, Any]]:
    url = f"{YAHOO_CHART_URL}{provider_symbol}"
    params = {"interval": "1d", "range": "18mo"}
    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
        data = response.json()
    except httpx.ProxyError:
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True, trust_env=False) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
            data = response.json()
        except Exception:
            raise ValueError("종목 시세를 불러오지 못했어. 잠시 후 다시 시도해줘.")
    except Exception:
        raise ValueError("종목 시세를 불러오지 못했어. 잠시 후 다시 시도해줘.")
    chart = data.get("chart", {})
    if chart.get("error"):
        raise ValueError("해당 종목 코드를 찾지 못했어.")
    result = chart.get("result") or []
    if not result:
        raise ValueError("해당 종목 코드를 찾지 못했어.")
    first = result[0]
    timestamps = first.get("timestamp") or []
    quote = (((first.get("indicators") or {}).get("quote")) or [{}])[0]
    opens = quote.get("open") or []
    highs = quote.get("high") or []
    lows = quote.get("low") or []
    closes = quote.get("close") or []
    volumes = quote.get("volume") or []

    prices: List[Dict[str, Any]] = []
    for ts, o, h, l, c, v in zip(timestamps, opens, highs, lows, closes, volumes):
        if o is None or h is None or l is None or c is None or v is None:
            continue
        prices.append(
            {
                "time": pd.to_datetime(ts, unit="s").strftime("%Y-%m-%d"),
                "open": float(o),
                "high": float(h),
                "low": float(l),
                "close": float(c),
                "volume": float(v),
            }
        )
    if len(prices) < 120:
        raise ValueError("분석 가능한 기간의 시세를 찾지 못했어. 다른 종목명/코드로 다시 입력해줘.")
    return prices[-240:]


def _parse_naver_chart_rows(raw_text: str) -> List[List[Any]]:
    text = raw_text.strip()
    if not text:
        return []
    try:
        parsed = ast.literal_eval(text)
    except Exception:
        return []
    return parsed if isinstance(parsed, list) else []


async def fetch_kr_daily_prices_from_naver(provider_symbol: str) -> List[Dict[str, Any]]:
    code = provider_symbol.strip().zfill(6)
    today = date.today()
    start_day = today - timedelta(days=900)
    params = {
        "symbol": code,
        "requestType": "1",
        "startTime": start_day.strftime("%Y%m%d"),
        "endTime": today.strftime("%Y%m%d"),
        "timeframe": "day",
    }
    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            response = await client.get(
                NAVER_KR_CHART_URL,
                params=params,
                headers={"User-Agent": "Mozilla/5.0 (ProjectLuna KR Fetcher)"},
            )
            response.raise_for_status()
        rows = _parse_naver_chart_rows(response.text)
    except Exception as e:
        logger.warning("KR price fetch failed for %s: %s", code, e)
        raise ValueError("국내 종목 시세를 불러오지 못했어. 잠시 후 다시 시도해줘.")

    if len(rows) <= 1:
        raise ValueError("입력한 국내 종목을 찾지 못했어. 종목명이나 종목코드를 다시 확인해줘.")

    prices: List[Dict[str, Any]] = []
    for row in rows[1:]:
        if not isinstance(row, list) or len(row) < 6:
            continue
        try:
            day = str(row[0])
            o = float(row[1])
            h = float(row[2])
            l = float(row[3])
            c = float(row[4])
            v = float(row[5])
            if not day or any(value <= 0 for value in [o, h, l, c]):
                continue
        except Exception:
            continue

        prices.append(
            {
                "time": pd.to_datetime(day, format="%Y%m%d").strftime("%Y-%m-%d"),
                "open": o,
                "high": h,
                "low": l,
                "close": c,
                "volume": v,
            }
        )

    if len(prices) < 120:
        raise ValueError("분석 가능한 기간의 시세를 찾지 못했어. 다른 종목명/코드로 다시 입력해줘.")
    return prices[-240:]


def _get_kis_credentials() -> tuple[str, str]:
    app_key = (os.getenv("KIS_APP_KEY") or "").strip()
    app_secret = (os.getenv("KIS_APP_SECRET") or "").strip()
    if not app_key or not app_secret:
        raise ValueError("KIS 인증 정보가 설정되지 않았어. 서버 환경의 KIS_APP_KEY/KIS_APP_SECRET을 확인해줘.")
    return app_key, app_secret


def _extract_kis_token_expiry_seconds(payload: Dict[str, Any]) -> int:
    expires_in = payload.get("expires_in")
    try:
        return max(int(float(expires_in)), 0)
    except Exception:
        return 0


async def _get_kis_access_token() -> str:
    now = time.time()
    cached = str(_KIS_TOKEN_CACHE.get("access_token") or "").strip()
    expires_at = float(_KIS_TOKEN_CACHE.get("expires_at") or 0.0)
    if cached and now < expires_at - 30:
        return cached

    app_key, app_secret = _get_kis_credentials()
    body = {
        "grant_type": "client_credentials",
        "appkey": app_key,
        "appsecret": app_secret,
    }

    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            response = await client.post(f"{KIS_BASE_URL}/oauth2/tokenP", json=body)
            response.raise_for_status()
        data = response.json()
    except Exception as e:
        logger.warning("KIS token fetch failed: %s", e)
        raise ValueError("KIS 인증 토큰 발급에 실패했어.")

    token = str(data.get("access_token") or "").strip()
    if not token:
        raise ValueError("KIS 인증 토큰이 비어 있어.")

    expires_in = _extract_kis_token_expiry_seconds(data) or 3600
    _KIS_TOKEN_CACHE["access_token"] = token
    _KIS_TOKEN_CACHE["expires_at"] = now + expires_in
    return token


def _normalize_us_provider_symbol(provider_symbol: str) -> str:
    symbol = provider_symbol.strip().upper()
    for suffix in (".US", ".KS", ".KQ"):
        if symbol.endswith(suffix):
            symbol = symbol[: -len(suffix)]
    return symbol


async def _kis_get_json(path: str, params: Dict[str, Any], tr_id: str) -> Dict[str, Any]:
    app_key, app_secret = _get_kis_credentials()
    access_token = await _get_kis_access_token()
    headers = {
        "authorization": f"Bearer {access_token}",
        "appkey": app_key,
        "appsecret": app_secret,
        "tr_id": tr_id,
        "custtype": "P",
    }
    url = f"{KIS_BASE_URL}{path}"
    logger.info("KIS request start path=%s tr_id=%s params=%s", path, tr_id, params)
    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            response = await client.get(url, headers=headers, params=params)
        try:
            payload = response.json()
        except Exception:
            payload = {}
        if not isinstance(payload, dict):
            payload = {}

        top_keys = sorted(payload.keys())
        logger.info(
            "KIS request done path=%s tr_id=%s status=%s keys=%s rt_cd=%s msg_cd=%s msg1=%s has_output=%s has_output1=%s has_output2=%s",
            path,
            tr_id,
            response.status_code,
            top_keys,
            payload.get("rt_cd"),
            payload.get("msg_cd"),
            payload.get("msg1"),
            "output" in payload,
            "output1" in payload,
            "output2" in payload,
        )
        response.raise_for_status()
        return payload
    except Exception as e:
        logger.warning("KIS request failed path=%s tr_id=%s params=%s error=%s", path, tr_id, params, e)
        raise


def _extract_kis_rows(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    outputs = payload.get("output2")
    if isinstance(outputs, list):
        return [row for row in outputs if isinstance(row, dict)]
    outputs = payload.get("output1")
    if isinstance(outputs, list):
        return [row for row in outputs if isinstance(row, dict)]
    output = payload.get("output")
    if isinstance(output, list):
        return [row for row in output if isinstance(row, dict)]
    return []


def _parse_kis_daily_price_row(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    raw_day = str(row.get("xymd") or row.get("stck_bsop_date") or row.get("date") or "").strip()
    if not raw_day:
        return None
    day = pd.to_datetime(raw_day, errors="coerce")
    if pd.isna(day):
        return None

    def _to_float(*keys: str) -> Optional[float]:
        for key in keys:
            value = row.get(key)
            if value in (None, ""):
                continue
            try:
                return float(str(value).replace(",", ""))
            except Exception:
                continue
        return None

    opened = _to_float("open", "stck_oprc", "ovrs_nmix_oprc")
    high = _to_float("high", "stck_hgpr", "ovrs_nmix_hgpr")
    low = _to_float("low", "stck_lwpr", "ovrs_nmix_lwpr")
    close = _to_float("clos", "close", "stck_clpr", "ovrs_nmix_prpr")
    volume = _to_float("tvol", "acml_vol", "ovrs_cvol_vol") or 0.0
    if any(value is None for value in (opened, high, low, close)):
        return None
    if min(opened or 0.0, high or 0.0, low or 0.0, close or 0.0) <= 0:
        return None
    return {
        "time": day.strftime("%Y-%m-%d"),
        "open": float(opened),
        "high": float(high),
        "low": float(low),
        "close": float(close),
        "volume": float(volume),
    }


async def fetch_us_daily_prices_from_kis(provider_symbol: str) -> List[Dict[str, Any]]:
    symbol = _normalize_us_provider_symbol(provider_symbol)
    if not re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,9}", symbol):
        raise ValueError("입력한 해외 종목 코드를 찾지 못했어. 티커를 다시 확인해줘.")

    exchange_candidates = ("NAS", "NYS", "AMS")
    path = "/uapi/overseas-price/v1/quotations/dailyprice"
    logger.info("US KIS fetch start symbol=%s exchanges=%s", symbol, ",".join(exchange_candidates))
    last_error: Optional[Exception] = None
    debug_failures: List[str] = []
    bimd = datetime.now(timezone.utc).strftime("%Y%m%d")

    for exchange in exchange_candidates:
        params = {"AUTH": "", "EXCD": exchange, "SYMB": symbol, "GUBN": "0", "BYMD": bimd, "MODP": "0"}
        try:
            payload = await _kis_get_json(path, params, tr_id="HHDFS76240000")
            rows = _extract_kis_rows(payload)
            rt_cd = payload.get("rt_cd")
            msg_cd = payload.get("msg_cd")
            msg1 = payload.get("msg1")
            logger.info(
                "US KIS payload summary symbol=%s exchange=%s row_count=%d has_output=%s has_output1=%s has_output2=%s",
                symbol,
                exchange,
                len(rows),
                "output" in payload,
                "output1" in payload,
                "output2" in payload,
            )
            parsed = [entry for row in rows if (entry := _parse_kis_daily_price_row(row))]
            parsed_count = len(parsed)
            logger.info(
                "US KIS parsed summary symbol=%s exchange=%s parsed_rows=%d",
                symbol,
                exchange,
                parsed_count,
            )
            parsed = sorted(parsed, key=lambda item: item["time"])
            if parsed_count >= 120:
                logger.info("US KIS fetch success symbol=%s exchange=%s rows=%d", symbol, exchange, len(parsed))
                return parsed[-240:]
            logger.info("US KIS fetch insufficient rows symbol=%s exchange=%s rows=%d", symbol, exchange, parsed_count)
            debug_failures.append(
                "exchange={exchange} reason=insufficient_rows parsed_rows={parsed_rows} row_count={row_count} "
                "rt_cd={rt_cd} msg_cd={msg_cd} msg1={msg1} has_output={has_output} has_output1={has_output1} has_output2={has_output2}".format(
                    exchange=exchange,
                    parsed_rows=parsed_count,
                    row_count=len(rows),
                    rt_cd=rt_cd,
                    msg_cd=msg_cd,
                    msg1=msg1,
                    has_output="output" in payload,
                    has_output1="output1" in payload,
                    has_output2="output2" in payload,
                )
            )
        except Exception as e:
            last_error = e
            logger.info("US KIS fetch failed symbol=%s exchange=%s error=%s", symbol, exchange, e)
            http_status = getattr(getattr(e, "response", None), "status_code", None)
            debug_failures.append(
                f"exchange={exchange} reason=exception http_status={http_status} error={type(e).__name__}: {e}"
            )

    if last_error or debug_failures:
        # TEMP DEBUG: include detailed KIS failure context directly in API error detail.
        raise ValueError(
            "미국 종목 시세를 KIS에서 불러오지 못했어. 잠시 후 다시 시도해줘. "
            f"[TEMP DEBUG] symbol={symbol} bimd={bimd} failures={' | '.join(debug_failures)}"
        )
    raise ValueError("입력한 해외 종목을 찾지 못했어. 티커를 다시 확인해줘.")


async def fetch_prices_for_instrument(instrument: Dict[str, str]) -> List[Dict[str, Any]]:
    provider = instrument["provider"]
    provider_symbol = instrument["provider_symbol"]
    logger.info(
        "Price provider selection symbol=%s market=%s country=%s provider=%s provider_symbol=%s",
        instrument.get("symbol"),
        instrument.get("market"),
        instrument.get("country"),
        provider,
        provider_symbol,
    )
    if provider == "kis" and instrument.get("country") == "US":
        return await fetch_us_daily_prices_from_kis(provider_symbol)
    if provider == "naver":
        return await fetch_kr_daily_prices_from_naver(provider_symbol)
    if provider == "yahoo":
        return await fetch_yahoo_daily_prices(provider_symbol)
    try:
        return await fetch_daily_prices(provider_symbol)
    except Exception:
        return await fetch_yahoo_daily_prices(instrument["symbol"])


def build_recent_trend_summary(df: pd.DataFrame) -> str:
    latest = float(df.iloc[-1]["close"])
    prev_5 = float(df.iloc[-6]["close"]) if len(df) >= 6 else latest
    prev_20 = float(df.iloc[-21]["close"]) if len(df) >= 21 else latest

    change_5 = ((latest - prev_5) / prev_5 * 100) if prev_5 else 0
    change_20 = ((latest - prev_20) / prev_20 * 100) if prev_20 else 0

    if change_5 > 4 and change_20 > 8:
        return f"최근 5일과 20일 흐름이 모두 강하고, 단기 상승 탄력이 살아 있는 편이야. 5일 기준 {change_5:.1f}%, 20일 기준 {change_20:.1f}% 움직였어."
    if change_5 < -4 and change_20 < -8:
        return f"최근 5일과 20일 흐름이 모두 약해서 단기 조정 압력이 큰 편이야. 5일 기준 {change_5:.1f}%, 20일 기준 {change_20:.1f}% 움직였어."
    if change_5 > 0 and change_20 > 0:
        return f"큰 추세는 아직 버티고 있는데, 최근엔 완만하게 우상향하는 흐름이야. 5일 기준 {change_5:.1f}%, 20일 기준 {change_20:.1f}% 움직였어."
    if change_5 < 0 < change_20:
        return f"중기 흐름은 살아 있지만 최근 5일은 눌림이 들어온 상태야. 5일 기준 {change_5:.1f}%, 20일 기준 {change_20:.1f}% 움직였어."
    return f"단기와 중기 흐름이 섞여 있어서 방향성이 아주 강하진 않아. 5일 기준 {change_5:.1f}%, 20일 기준 {change_20:.1f}% 움직였어."


def classify_trend_state(change_percent: float, recent_move_percent_5: float, daily_range_percent: float, ma20_gap_percent: float) -> str:
    if change_percent <= -4.0 or (recent_move_percent_5 <= -8.0 and ma20_gap_percent <= -1.0):
        return "sharp_drop"
    if change_percent >= 4.0 or (recent_move_percent_5 >= 8.0 and ma20_gap_percent >= 1.0):
        return "sharp_rise"
    if abs(change_percent) <= 1.2 and daily_range_percent <= 2.2:
        return "range"
    return "normal"


def _parse_timestamp_to_epoch_seconds(raw_value: Any) -> Optional[float]:
    if raw_value is None:
        return None

    if isinstance(raw_value, datetime):
        if raw_value.tzinfo is None:
            return raw_value.replace(tzinfo=timezone.utc).timestamp()
        return raw_value.timestamp()

    if isinstance(raw_value, (int, float)):
        value = float(raw_value)
        if value > 1_000_000_000_000:
            return value / 1000.0
        return value

    if isinstance(raw_value, str):
        text = raw_value.strip()
        if not text:
            return None
        try:
            return _parse_timestamp_to_epoch_seconds(float(text))
        except ValueError:
            pass
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return None
    return None


def _format_epoch_seconds(raw_seconds: Optional[float]) -> Optional[str]:
    if raw_seconds is None:
        return None
    return datetime.fromtimestamp(raw_seconds, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def select_realtime_quote(
    symbol: str,
    *,
    quote_cache: Optional[Dict[str, Any]] = None,
    now_ts: Optional[float] = None,
    max_age_seconds: float = REALTIME_QUOTE_MAX_AGE_SECONDS,
) -> Dict[str, Any]:
    metadata = {
        "quote": None,
        "currentPriceSource": "historical_fallback",
        "currentPriceTimestamp": None,
        "realtimeApplied": False,
        "realtimeStale": False,
    }

    if quote_cache is None:
        cache_candidates = (
            getattr(app.state, "kis_realtime_quotes", None),
            getattr(app.state, "realtime_quote_cache", None),
            getattr(app.state, "quote_cache", None),
        )
        quote_cache = next((candidate for candidate in cache_candidates if isinstance(candidate, dict)), None)

    if not quote_cache:
        return metadata

    raw_entry = quote_cache.get(symbol) or quote_cache.get(symbol.upper()) or quote_cache.get(symbol.lower())
    if not isinstance(raw_entry, dict):
        return metadata

    price_raw = raw_entry.get("price", raw_entry.get("currentPrice", raw_entry.get("lastPrice")))
    try:
        price_value = float(price_raw)
    except (TypeError, ValueError):
        return metadata

    if price_value <= 0:
        return metadata

    received_ts = _parse_timestamp_to_epoch_seconds(
        raw_entry.get("received_at", raw_entry.get("receivedAt", raw_entry.get("timestamp")))
    )
    if received_ts is None:
        return metadata

    current_now_ts = float(now_ts if now_ts is not None else time.time())
    quote_age_seconds = current_now_ts - received_ts
    metadata["currentPriceTimestamp"] = _format_epoch_seconds(received_ts)

    if quote_age_seconds > max_age_seconds:
        metadata["realtimeStale"] = True
        return metadata

    metadata["quote"] = {
        "price": price_value,
        "timestamp": received_ts,
    }
    metadata["currentPriceSource"] = "kis_realtime"
    metadata["realtimeApplied"] = True
    return metadata


def recalculate_summary_for_current_price(summary: Dict[str, Any], current_price: float) -> Dict[str, Any]:
    next_summary = dict(summary)
    prior_current_price = float(next_summary.get("currentPrice", current_price) or current_price)
    prev_close = float(next_summary.get("prevClose", prior_current_price) or prior_current_price)

    next_summary["currentPrice"] = round(float(current_price), 2)
    next_summary["prevClose"] = round(prev_close, 2)

    if prev_close:
        next_summary["changePercent"] = round(((float(current_price) - prev_close) / prev_close) * 100, 2)

    day_high = next_summary.get("dayHigh")
    day_low = next_summary.get("dayLow")
    if day_high is not None and day_low is not None and float(current_price):
        next_summary["dailyRangePercent"] = round(((float(day_high) - float(day_low)) / float(current_price)) * 100, 2)
    elif next_summary.get("dailyRangePercent") is not None and prior_current_price:
        spread_amount = (float(next_summary["dailyRangePercent"]) / 100.0) * prior_current_price
        next_summary["dailyRangePercent"] = round((spread_amount / float(current_price)) * 100, 2) if float(current_price) else 0.0

    recent_move_percent_5 = next_summary.get("recentMovePercent5")
    if recent_move_percent_5 is not None:
        denominator = 1 + (float(recent_move_percent_5) / 100.0)
        if denominator:
            recent_5_close = prior_current_price / denominator
            if recent_5_close:
                next_summary["recentMovePercent5"] = round(((float(current_price) - recent_5_close) / recent_5_close) * 100, 2)

    ma20 = next_summary.get("ma20")
    ma20_gap_percent = ((float(current_price) - float(ma20)) / float(ma20) * 100) if ma20 else 0.0
    if (
        next_summary.get("changePercent") is not None
        and next_summary.get("recentMovePercent5") is not None
        and next_summary.get("dailyRangePercent") is not None
    ):
        next_summary["trendState"] = classify_trend_state(
            float(next_summary["changePercent"]),
            float(next_summary["recentMovePercent5"]),
            float(next_summary["dailyRangePercent"]),
            ma20_gap_percent,
        )

    support = next_summary.get("support")
    resistance = next_summary.get("resistance")
    if support is not None:
        support_broken = float(current_price) < float(support)
        next_summary["supportBroken"] = support_broken
        next_summary["reclaimLevel"] = round(float(support), 2) if support_broken else None
        next_summary["supportRole"] = "reclaim_resistance" if support_broken else "active_support"
    if resistance is not None:
        resistance_broken = float(current_price) > float(resistance) * 1.005
        next_summary["resistanceBroken"] = resistance_broken
        next_summary["breakoutLevel"] = round(float(resistance), 2) if resistance_broken else None
        next_summary["resistanceRole"] = "breakout_support" if resistance_broken else "active_resistance"

    return next_summary


def build_analysis(prices: List[Dict[str, Any]]) -> Dict[str, Any]:
    if len(prices) < 120:
        raise ValueError("분석하려면 최소 120일 정도 데이터가 필요해")

    df = pd.DataFrame(prices).copy()
    df["ma5"] = df["close"].rolling(5).mean()
    df["ma20"] = df["close"].rolling(20).mean()
    df["ma60"] = df["close"].rolling(60).mean()
    df["ma120"] = df["close"].rolling(120).mean()
    df["vol20"] = df["volume"].rolling(20).mean()

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    current_price = float(latest["close"])
    prev_close = float(prev["close"]) if pd.notna(prev["close"]) else current_price
    change_percent = ((current_price - prev_close) / prev_close * 100) if prev_close else 0.0
    daily_range_percent = ((float(latest["high"]) - float(latest["low"])) / current_price * 100) if current_price else 0.0
    ma5 = float(latest["ma5"]) if pd.notna(latest["ma5"]) else current_price
    ma20 = float(latest["ma20"]) if pd.notna(latest["ma20"]) else current_price
    ma60 = float(latest["ma60"]) if pd.notna(latest["ma60"]) else current_price
    ma120 = float(latest["ma120"]) if pd.notna(latest["ma120"]) else current_price

    recent_20_high = float(df["high"].tail(20).max())
    recent_20_low = float(df["low"].tail(20).min())
    recent_60_high = float(df["high"].tail(60).max())
    recent_60_low = float(df["low"].tail(60).min())

    avg_volume = float(latest["vol20"]) if pd.notna(latest["vol20"]) else float(latest["volume"])
    volume_ratio = float(latest["volume"] / avg_volume) if avg_volume > 0 else 1.0

    support_candidates = sorted(
        {
            round(recent_20_low, 2),
            round(ma20, 2),
            round(ma60, 2),
        }
    )
    resistance_candidates = sorted(
        {
            round(recent_20_high, 2),
            round(recent_60_high, 2),
        }
    )

    min_separation_pct = 0.005

    def _is_too_close(a: Optional[float], b: Optional[float]) -> bool:
        if a is None or b is None:
            return False
        base = max(abs(a), abs(b), 1e-9)
        return abs(a - b) / base <= min_separation_pct

    support = round(max(recent_20_low, ma20), 2)
    support_broken = current_price < support
    reclaim_level: Optional[float] = round(support, 2) if support_broken else None

    lower_support_pool = sorted(
        {
            round(recent_20_low, 2),
            round(recent_60_low, 2),
            round(ma20, 2),
            round(ma60, 2),
            round(ma120, 2),
        }
    )
    valid_lower_supports = [level for level in lower_support_pool if level <= current_price * 0.995]
    if support_broken:
        fallback_support = round(min(recent_20_low, recent_60_low, current_price * 0.95), 2)
        active_support = round(max(valid_lower_supports), 2) if valid_lower_supports else fallback_support
    else:
        active_support = round(support, 2)

    base_resistance_pool = sorted(
        {
            round(recent_20_high, 2),
            round(recent_60_high, 2),
            round(ma20, 2),
            round(ma60, 2),
            round(ma120, 2),
        }
    )
    resistance_pool = sorted(
        {
            *base_resistance_pool,
            *([reclaim_level] if reclaim_level is not None else []),
        }
    )
    upside_resistance = [level for level in base_resistance_pool if level >= current_price * 1.005]
    original_resistance = round(min(upside_resistance), 2) if upside_resistance else round(max(base_resistance_pool), 2)
    resistance_broken = current_price > original_resistance * 1.005
    breakout_level: Optional[float] = round(original_resistance, 2) if resistance_broken else None
    if resistance_broken:
        higher_resistances = [level for level in resistance_pool if level >= current_price * 1.005]
        fallback_resistance = round(max(current_price * 1.03, original_resistance * 1.01), 2)
        active_resistance = round(min(higher_resistances), 2) if higher_resistances else fallback_resistance
    else:
        active_resistance = round(original_resistance, 2)

    lower_support_candidates = sorted(
        {
            level
            for level in lower_support_pool
            if level <= current_price * 0.995 and (reclaim_level is None or level < reclaim_level)
        },
        reverse=True,
    )

    if support_broken and _is_too_close(active_support, reclaim_level):
        next_support = next((lvl for lvl in lower_support_candidates if not _is_too_close(lvl, reclaim_level)), None)
        if next_support is not None:
            active_support = round(next_support, 2)

    if support_broken and reclaim_level is not None and _is_too_close(active_resistance, reclaim_level):
        active_resistance = round(reclaim_level, 2)

    if _is_too_close(active_support, active_resistance):
        next_support = next((lvl for lvl in lower_support_candidates if not _is_too_close(lvl, active_resistance)), None)
        if next_support is not None:
            active_support = round(next_support, 2)
        else:
            higher_resistance_candidates = sorted(
                {level for level in resistance_pool if level >= max(current_price * 1.005, active_resistance * 1.005)}
            )
            next_resistance = next(
                (lvl for lvl in higher_resistance_candidates if not _is_too_close(lvl, active_support)),
                None,
            )
            if next_resistance is not None:
                active_resistance = round(next_resistance, 2)
            else:
                active_resistance = round(max(active_resistance, current_price * 1.03), 2)

    resistance = round(active_resistance, 2)

    above_ma20 = current_price > ma20
    above_ma60 = current_price > ma60
    strong_volume = volume_ratio >= 1.3
    near_breakout = current_price >= recent_20_high * 0.985
    pullback_zone = above_ma20 and current_price < recent_20_high * 0.97
    breakdown = bool(current_price < ma20 and pd.notna(prev["ma20"]) and prev["close"] >= prev["ma20"])
    recent_5_close = float(df.iloc[-6]["close"]) if len(df) >= 6 else current_price
    recent_move_percent_5 = ((current_price - recent_5_close) / recent_5_close * 100) if recent_5_close else 0.0
    ma20_gap_percent = ((current_price - ma20) / ma20 * 100) if ma20 else 0.0
    trend_state = classify_trend_state(change_percent, recent_move_percent_5, daily_range_percent, ma20_gap_percent)

    if near_breakout and strong_volume and above_ma20:
        state = "돌파 시도"
    elif pullback_zone and above_ma20 and above_ma60:
        state = "눌림 구간"
    elif breakdown:
        state = "관망"
    elif current_price >= recent_60_high * 0.99:
        state = "추격 주의"
    else:
        state = "박스권"

    if volume_ratio >= 1.6:
        volume_summary = f"거래량이 평균 대비 {volume_ratio:.2f}배로 꽤 강하게 붙어 있어."
    elif volume_ratio >= 1.15:
        volume_summary = f"거래량이 평균 대비 {volume_ratio:.2f}배 정도라 관심은 붙고 있어."
    elif volume_ratio <= 0.8:
        volume_summary = f"거래량이 평균 대비 {volume_ratio:.2f}배 수준이라 힘은 아직 약한 편이야."
    else:
        volume_summary = f"거래량은 평균 대비 {volume_ratio:.2f}배로 무난한 수준이야."

    recent_trend_summary = build_recent_trend_summary(df)

    chart_df = df.tail(65).copy()

    candles = []
    ma5_chart = []
    ma20_chart = []
    ma60_chart = []
    ma120_chart = []
    volume_chart = []

    for _, row in chart_df.iterrows():
        candles.append(
            {
                "time": row["time"],
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
            }
        )
        volume_chart.append(
            {
                "time": row["time"],
                "value": float(row["volume"]),
                "color": "rgba(96,165,250,0.45)" if float(row["close"]) >= float(row["open"]) else "rgba(248,113,113,0.45)",
            }
        )

        if pd.notna(row["ma5"]):
            ma5_chart.append({"time": row["time"], "value": round(float(row["ma5"]), 2)})
        if pd.notna(row["ma20"]):
            ma20_chart.append({"time": row["time"], "value": round(float(row["ma20"]), 2)})
        if pd.notna(row["ma60"]):
            ma60_chart.append({"time": row["time"], "value": round(float(row["ma60"]), 2)})
        if pd.notna(row["ma120"]):
            ma120_chart.append({"time": row["time"], "value": round(float(row["ma120"]), 2)})

    return {
        "summary": {
            "currentPrice": round(current_price, 2),
            "prevClose": round(prev_close, 2),
            "changePercent": round(change_percent, 2),
            "dayHigh": round(float(latest["high"]), 2),
            "dayLow": round(float(latest["low"]), 2),
            "dailyRangePercent": round(daily_range_percent, 2),
            "recentMovePercent5": round(recent_move_percent_5, 2),
            "trendState": trend_state,
            "ma5": round(ma5, 2),
            "ma20": round(ma20, 2),
            "ma60": round(ma60, 2),
            "ma120": round(ma120, 2),
            "support": support,
            "supportBroken": support_broken,
            "activeSupport": active_support,
            "reclaimLevel": reclaim_level,
            "supportRole": "reclaim_resistance" if support_broken else "active_support",
            "resistance": resistance,
            "resistanceBroken": resistance_broken,
            "activeResistance": active_resistance,
            "breakoutLevel": breakout_level,
            "resistanceRole": "breakout_support" if resistance_broken else "active_resistance",
            "state": state,
            "volumeRatio": round(volume_ratio, 2),
            "rangeHigh20": round(recent_20_high, 2),
            "rangeLow20": round(recent_20_low, 2),
            "rangeHigh60": round(recent_60_high, 2),
            "rangeLow60": round(recent_60_low, 2),
        },
        "trendSummary": recent_trend_summary,
        "volumeSummary": volume_summary,
        "supportCandidates": support_candidates,
        "resistanceCandidates": resistance_candidates,
        "chart": {
            "candles": candles,
            "ma5": ma5_chart,
            "ma20": ma20_chart,
            "ma60": ma60_chart,
            "ma120": ma120_chart,
            "volume": volume_chart,
        },
    }


def build_state_hint(summary: Dict[str, Any], has_position: bool, avg_price: Optional[float], style: str) -> str:
    current = summary["currentPrice"]
    support = summary.get("activeSupport", summary["support"])
    resistance = summary.get("activeResistance", summary["resistance"])
    state = summary["state"]
    ma20 = summary["ma20"]
    trend_state = summary.get("trendState")

    if trend_state == "sharp_drop":
        return "급락 방어 우선 구간"

    if has_position and avg_price is not None:
        pnl = ((current - avg_price) / avg_price) * 100 if avg_price else 0
        if pnl >= 10 and current < resistance * 0.99:
            return "수익 관리 구간"
        if current < support and current < ma20:
            return "손절 판단 구간"
        if abs(current - support) / support <= 0.02:
            return "눌림 확인 구간"
        if pnl > 0 and style in {"protect_profit", "trend_partial"}:
            return "반등 시 매도 우선 구간"

    if not has_position:
        if state == "추격 주의":
            return "추격 금지 구간"
        if state == "관망":
            return "박스권 관망 구간"
        if state == "눌림 구간":
            return "눌림 매수 대기 구간"
        if state == "돌파 시도":
            return "돌파 시도 구간"

    if state == "돌파 시도":
        return "돌파 시도 구간"
    if state == "눌림 구간":
        return "눌림 매수 대기 구간"
    if state == "관망":
        return "박스권 관망 구간"
    return "중립 관망 구간"


def build_personalization(
    mode: str,
    current_price: float,
    support: float,
    resistance: float,
    avg_price: Optional[float],
    quantity: Optional[int],
    style: str,
) -> Dict[str, Any]:
    has_position = mode == "holder"

    style_info = STYLE_GUIDE.get(style, STYLE_GUIDE["conservative"])

    pnl_amount = None
    pnl_percent = None
    if has_position and avg_price is not None and quantity is not None and quantity > 0:
        pnl_amount = round((current_price - avg_price) * quantity, 2)
        pnl_percent = round(((current_price - avg_price) / avg_price) * 100, 2) if avg_price else None

    add_buy_zone = round(min(support, current_price * 0.98), 2)
    stop_line = round(min(support * 0.98, current_price * 0.96), 2)
    first_take_profit = round(resistance, 2)

    return {
        "mode": mode,
        "hasPosition": has_position,
        "avgPrice": avg_price if has_position else None,
        "quantity": quantity if has_position else None,
        "pnlAmount": pnl_amount if has_position else None,
        "pnlPercent": pnl_percent if has_position else None,
        "style": style,
        "styleLabel": style_info["label"],
        "styleDescription": style_info["description"],
        "holderView": "보유자" if has_position else "미보유자",
        "suggestedAddBuyZone": add_buy_zone,
        "suggestedStop": stop_line,
        "suggestedTakeProfit": first_take_profit,
    }


def _safe_json_parse(raw: str) -> Optional[Dict[str, Any]]:
    raw = raw.strip()
    if not raw:
        return None

    try:
        loaded = json.loads(raw)
        if isinstance(loaded, dict):
            return loaded
        if isinstance(loaded, str):
            loaded_nested = json.loads(loaded)
            if isinstance(loaded_nested, dict):
                return loaded_nested
    except Exception:
        pass

    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:].strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1:
        return None
    candidate = raw[start : end + 1]
    try:
        return json.loads(candidate)
    except Exception:
        return None


def _preview_text(raw: str, limit: int = 240) -> str:
    compact = " ".join(raw.split())
    if len(compact) <= limit:
        return compact
    return f"{compact[:limit]}…"


def _extract_message_content(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks: list[str] = []
        for part in content:
            if isinstance(part, str):
                chunks.append(part)
                continue
            if isinstance(part, dict):
                for key in ("text", "content", "output_text"):
                    value = part.get(key)
                    if isinstance(value, str) and value.strip():
                        chunks.append(value)
                        break
                continue
            text_attr = getattr(part, "text", None)
            if isinstance(text_attr, str) and text_attr.strip():
                chunks.append(text_attr)
                continue
            if hasattr(part, "model_dump"):
                dumped = part.model_dump()
                if isinstance(dumped, dict):
                    for key in ("text", "content", "output_text"):
                        value = dumped.get(key)
                        if isinstance(value, str) and value.strip():
                            chunks.append(value)
                            break
        return "\n".join(chunks).strip()
    if isinstance(content, dict):
        for key in ("text", "content", "output_text"):
            value = content.get(key)
            if isinstance(value, str):
                return value
    return str(content)


def _has_forbidden_tone(text: str) -> bool:
    banned = [
        "해라",
        "하지 마라",
        "해야 한다",
        "구간입니다",
        "보수적 접근",
        "리스크 관리",
        "매수 관점",
        "단기적으로 변동성",
    ]
    return any(token in text for token in banned)


def _fallback_ai_opinion(summary: Dict[str, Any]) -> Dict[str, str]:
    trend_state = summary.get("trendState", "normal")
    support_broken = bool(summary.get("supportBroken"))
    active_support = summary.get("activeSupport", summary.get("support"))
    reclaim_level = summary.get("reclaimLevel")
    resistance_broken = bool(summary.get("resistanceBroken"))
    active_resistance = summary.get("activeResistance", summary.get("resistance"))
    breakout_level = summary.get("breakoutLevel")

    if trend_state == "sharp_drop":
        if support_broken and reclaim_level is not None:
            return {
                "summary": "급락 뒤 지지까지 밀려서 일단 수익보다 방어 기준이 먼저야.",
                "commentary": (
                    f"{reclaim_level}은 원래 지지였는데 이미 깨져서 되돌림 때 매도 물량이 나올 확률이 커. "
                    f"반등이 나와도 {reclaim_level}을 다시 올려놓기 전엔 추격하지 말고, 아래에선 {active_support} 지키는지부터 보자. "
                    f"보유 중이면 {active_support}가 흔들릴 때 공포 매도가 더 붙기 쉬우니 비중 먼저 가볍게 맞추는 게 좋아."
                ),
            }
        return {
            "summary": "급락 구간이라 욕심내기보다 방어 신호 확인이 먼저야.",
            "commentary": (
                f"오늘 {summary.get('changePercent', 0)}% 밀리면서 기대가 꺾여서 반등마다 정리 매물이 나올 수 있어. "
                f"{active_support}에서 반등이 붙고 거래량이 살아나는 장면 전까지는 무리해서 들어가지 말고 기다리자. "
                f"보유 중이면 {active_support} 이탈 때 불안 매도가 한 번 더 나올 수 있으니 축소 기준을 먼저 정해두는 게 안전해."
            ),
        }
    if support_broken and reclaim_level is not None:
        return {
            "summary": "기존 지지는 이미 깨져서 지금은 회복 여부를 먼저 봐야 해.",
            "commentary": (
                f"{reclaim_level}은 원래 지지였지만 지금은 되돌림 저항에 가까워서 회복 전엔 공격적으로 보기 어려워. "
                f"아래에선 {active_support}이 다음 지지 후보고, 위쪽에서 실제로 막히는 자리는 {active_resistance} 쪽이야. "
                "급하게 추격하지 말고 회복 캔들이랑 거래량 붙는지부터 같이 보자."
            ),
        }
    if resistance_broken and breakout_level is not None:
        return {
            "summary": "기존 저항은 이미 돌파해서 이제는 눌림 지지 확인이 더 중요해.",
            "commentary": (
                f"{breakout_level}은 원래 저항이었는데 이미 돌파한 자리라 눌릴 때 지지로 버티는지 보는 게 핵심이야. "
                f"위쪽에서 새로 막힐 수 있는 자리는 {active_resistance} 근처라 그 전까지는 추세 유지 쪽으로 볼 수 있어. "
                f"다만 {breakout_level} 재이탈이 나오면 돌파 실패가 될 수 있으니 대응 기준은 미리 잡아두자."
            ),
        }
    return {
        "summary": "지금은 급하게 판단하기보다 기준 자리 확인이 먼저야.",
        "commentary": (
            f"지금 가격은 {summary['currentPrice']} 근처고, 핵심은 {active_support} 지지랑 {active_resistance} 저항 반응이야. "
            f"거래량이 평균 대비 {summary['volumeRatio']}배라서 힘이 확 붙는 자리는 아직 더 확인해보는 게 좋아 보여. "
            "보유 중이면 지지 깨지는지만 먼저 보고, 미보유면 눌림이나 안착이 나오는지 같이 보자."
        ),
    }


def _normalize_ai_opinion_payload(payload: Dict[str, Any]) -> tuple[Optional[Dict[str, str]], Optional[str]]:
    summary = str(payload.get("summary", "")).strip()
    commentary = str(payload.get("commentary", "")).strip()
    if not summary or not commentary:
        return None, "missing_fields"
    summary = summary[:70].strip()
    commentary = commentary[:540].strip()
    if _has_forbidden_tone(summary) or _has_forbidden_tone(commentary):
        return None, "forbidden_tone"
    return {"summary": summary, "commentary": commentary}, None


def _build_style_behavior_prompt(style: str, has_position: bool) -> str:
    style_key = style if style in STYLE_GUIDE else "conservative"

    if has_position:
        holder_bias = {
            "conservative": (
                "행동 우선순위는 방어→유지→추가대응 순서로 둬. "
                "지지 이탈이나 추세 훼손 신호가 보이면 추가매수보다 먼저 비중 축소나 손절 기준을 분명히 제시해. "
                "애매할 땐 공격적 물타기 제안 대신 '일단 지키면서 확인' 쪽으로 결론을 내고, stopLine은 비교적 타이트하게 쓰게 해."
            ),
            "pullback": (
                "행동 우선순위는 눌림 반응 확인→선별적 추가매수→유지 순서로 잡아. "
                "추가매수는 support/addBuyZone 근처에서 반등 확인이 있을 때만 허용하고, 중간 가격대의 즉흥 추가는 피하게 해. "
                "상단에서 힘이 약해지면 무리한 추가 대신 좋은 평균단가를 다시 기다리게 유도해."
            ),
            "trend": (
                "행동 우선순위는 추세 유지 확인→보유 지속→실패 시 빠른 방어야. "
                "저항 돌파 후 안착이 유지되면 조기 익절 압박을 줄이고 보유 연장을 허용해. "
                "대신 돌파 실패나 재이탈이 나오면 늦게 버티지 말고 신속히 방어 전환하도록 써."
            ),
            "swing": (
                "짧은 호흡의 전술 대응이 핵심이야. "
                "보유 조언에서도 hold만 말하지 말고 지금 구간의 즉시 실행안(유지 조건, 빠른 stop, 근접 목표 도달 시 부분익절)을 분명히 제시해. "
                "손절과 목표가 간격은 상대적으로 짧고 선명하게, 대응 속도는 빠르게 잡아."
            ),
            "protect_profit": (
                "수익 구간에서는 기대수익 확대보다 이익 보전을 최우선으로 둬. "
                "pnlPercent가 플러스이면 부분익절이나 stop 상향(트레일링 성격)을 자연스럽게 우선 제안해. "
                "변동성 구간에서 수익 반납 가능성이 보이면 더 버티기보다 먼저 잠그는 결론으로 기울여."
            ),
            "trend_partial": (
                "핵심은 '일부는 익절, 일부는 추세 추종'의 동시 운용이야. "
                "추세가 살아 있으면 전량 매도보다 분할익절 후 잔여 물량 보유를 기본값으로 두고, "
                "남은 물량은 추세 훼손 시 정리할 기준을 같이 제시해."
            ),
        }
        return holder_bias[style_key]

    viewer_bias = {
        "conservative": (
            "행동 우선순위는 기다림→확인된 진입→예외적 대응 순서야. "
            "지지 반응 확인이나 저항 돌파 안착 중 하나도 명확하지 않으면 '지금은 굳이 서두르지 말자' 쪽으로 결론내. "
            "중간 구간 추격 진입은 억제하고, 확인 전 선진입은 거의 허용하지 마."
        ),
        "pullback": (
            "행동 우선순위는 눌림 대기→지지 반응 확인 후 진입→돌파 추종은 후순위로 둬. "
            "가격이 상단으로 늘어진 상태면 진입보다 '눌림 반응 나올 때 들어가는 게 더 좋다'는 방향을 기본값으로 해. "
            "돌파 추격은 거래량과 안착이 매우 선명할 때만 예외적으로 허용해."
        ),
        "trend": (
            "행동 우선순위는 돌파 확인→추세 추종 진입→실패 시 빠른 철수야. "
            "저항 위 재돌파 후 안착이 확인되면 '따라가는 진입 가능'으로 명확히 허용해. "
            "단, 확인 없는 맹목 추격은 금지하고 실패 시 빠른 stop 기준을 함께 제시해."
        ),
        "swing": (
            "짧은 트레이드 실행안을 최우선으로 제시해. "
            "진입 가능/대기를 빠르게 판단하고, 진입 시엔 entry-stop-target을 또렷하게 같이 말해. "
            "목표가와 손절가는 상대적으로 짧고 명확하게 잡아서 바로 실행 가능한 톤으로 유도해."
        ),
        "protect_profit": (
            "신규 진입은 매우 선별적으로 다뤄. "
            "손익비가 불리하거나 되돌림 리스크가 크면 매수 아이디어보다 관망을 우선 추천해. "
            "억지 진입을 만들지 말고, 낮은 리스크 구간에서만 제한적으로 진입 허용해."
        ),
        "trend_partial": (
            "추세 확인 진입은 허용하되, 처음부터 분할익절 계획을 포함해 제시해. "
            "즉 '들어가면 어디서 일부 정리하고 나머지는 추세로 본다'는 구조를 자연스럽게 포함해."
        ),
    }
    return viewer_bias[style_key]


def _build_mode_behavior_prompt(has_position: bool) -> str:
    if has_position:
        return (
            "보유자 기준으로 써. avgPrice, pnlPercent, 현재가와 평단 관계를 먼저 보고 지금 계좌 느낌을 친구처럼 한 줄로 말해줘. "
            "말투는 설명문이나 보고서처럼 딱딱하게 쓰지 말고, 지금 차트 같이 보면서 얘기하듯 자연스럽게 이어가. "
            "보유자 코멘트는 신규 진입 코칭처럼 들리면 안 돼. 이미 들고 있는 물량을 어떻게 지킬지에만 집중해. "
            "유지/추가매수(기존 포지션에 한정)/부분익절/손절 판단은 꼭 담되 항목처럼 나열하지 말고 한 흐름 안에서 연결하고, 가능하면 한 문장 안에서 행동과 이유를 같이 말해줘. "
            "추가매수를 권하면 '신규 진입'이 아니라 '기존 물량에 덧붙이는 추가 대응'으로 분명히 말하고, 가능할 때는 초기 추가 비중 가이드(예: 총 계획의 30~50%)와 확인 뒤 나머지 추가 계획을 함께 붙여서 실행 순서를 보여줘. "
            "익절을 권하면 가능할 때는 1차 목표에서 부분익절 비율(예: 20~30%)을 제시하고, 남은 물량은 추세/지지 훼손 전까지 보유할지까지 이어서 말해줘. "
            "리스크 관리는 모호하게 넘기지 말고, 어떤 가격/조건에서 손절 또는 비중 축소할지 조건을 분명하게 밝혀줘. "
            "다만 수치를 억지로 만들진 말고, 데이터상 자연스러울 때만 숫자를 붙여."
            "수익 구간이면 수익 보호와 분할익절을 자연스럽게 넣고, 손실·약세 구간이면 지지 지키는지와 이탈 시 정리 기준을 먼저 챙겨줘. "
            "addBuyZone, takeProfit, stopLine, support/resistance 가격 기준을 말에 녹여서 '여기선~ 대신 ~깨지면~' 같은 대화체로 풀고, 이유는 반드시 차트 근거와 매수/매도 심리를 같이 붙여줘. "
            "보유자 코멘트는 보통 4~8문장 안에서 자연스럽게 길어져도 되고, defend/hold/add/trim/cut 중 지금 필요한 행동을 흐름 안에서 분명히 보여줘. "
            "행동을 말할 때는 왜 그 자리에서 매수·매도가 나올지까지 같이 설명해줘(예: 급락 뒤 반등 때 물린 매도 출회, 지지 이탈 시 공포 매도, 저항 근처 차익실현). "
            "특히 기다림/진입/추가매수/부분익절/손절 같은 행동마다 심리를 빠짐없이 붙여서, 누가 왜 움직이고 그게 가격을 어떻게 흔드는지까지 바로 연결해줘. "
            "심리는 라벨처럼 짧게 끝내지 말고, 누가 왜 행동하는지까지 원인-결과로 풀어줘(예: 위에서 물린 사람들 매도 출회로 반등이 눌릴 수 있다). "
            "심리 설명이 빠지면 불완전한 답변이야. 마지막은 짧게 멘탈 케어 한마디로 마무리해."
        )
    return (
        "미보유자 기준으로 써. 지금이 대기인지 진입 가능한지부터 분명하게 말하되, 설명문처럼 정의하지 말고 친구가 옆에서 코칭하듯 말해줘. "
        "미보유자 코멘트는 '지금 들어가도 되는지/언제 들어갈지/얼마나 먼저 들어갈지'를 중심으로 써. 보유 물량 관리 조언처럼 흐리지 마. "
        "wait vs entry 판단은 꼭 보여주고, 언제 들어갈지는 눌림 가격대나 돌파 안착 조건으로 구체적으로 말해줘. "
        "눌림이면 '어느 근처에서 반응 나오면 들어간다', 돌파면 '어느 저항 위 안착 확인 후 따라간다'처럼 실전 문장으로 이어줘. "
        "진입을 열어줄 때는 가능하면 초기 진입 비중 가이드(예: 30~50%)를 덧붙이고, 확인 신호 뒤 나머지 비중을 더하는 계획까지 같이 말해줘. "
        "목표가 제시가 가능하면 1차 목표에서 일부(예: 20~30%) 먼저 이익실현하고 잔여 물량은 추세를 보며 운영하는 흐름을 넣어줘. "
        "리스크 관리는 반드시 손절/축소 조건을 명확한 가격 또는 차트 조건으로 제시해줘. "
        "단, 숫자는 억지로 채우지 말고 맥락상 자연스러울 때만 넣어."
        "지금 추격이 위험한 자리면 바로 따라붙지 말라고 자연스럽게 경고하고, 가능하면 한 문장 안에서 행동과 이유를 같이 말해줘. "
        "대기/진입/추격주의 각각의 이유는 차트 근거와 매수/매도 심리를 같이 붙여서 설명해줘(예: 거래량 약해 매수 확신 부족, 저항 근처 차익실현 매물, 지지 이탈 시 불안 매도). "
        "심리는 라벨처럼 짧게 끝내지 말고, 누가 왜 행동하는지까지 원인-결과로 풀어줘(예: 지지 이탈이라 불안한 매도가 겹치며 추가 하락 압력이 생길 수 있다). "
        "대기/진입/추격주의/손절가/목표가 제안 각각에 심리 근거를 꼭 붙여서, '왜 지금 그 행동이 맞는지'를 참여자 행동 중심으로 이해되게 말해줘. "
        "문장은 보통 4~8문장 안에서 살아있는 대화체로, 체크리스트처럼 끊지 말고 흐름 있게 써줘. "
        "심리 설명이 빠지면 답변이 완성되지 않은 거야. "
        "마지막엔 한 줄 정도 편하게 멘탈 케어를 섞어."
    )


def _build_system_prompt(has_position: bool, style: str) -> str:
    behavior_prompt = _build_mode_behavior_prompt(has_position)
    style_behavior_prompt = _build_style_behavior_prompt(style, has_position)
    return (
        "너는 Luna. 한국어 반말의 친근한 트레이딩 메이트 톤으로만 답해. "
        "반드시 JSON 객체 하나만 출력: {\"summary\":\"\", \"commentary\":\"\"}. "
        "summary는 1문장으로 고정하고, commentary는 보통 4~8문장으로 자연스럽게 써. "
        "숫자 안전 규칙을 최우선으로 지켜: 입력 JSON에 명시된 숫자만 사용하고, 입력에 없는 가격 숫자는 절대 추정/창작/보간하지 마. "
        "가격 숫자를 말할 땐 반드시 해당 필드(예: price, support, resistance, addBuyZone, stopLine, takeProfit, avgPrice, ma20, ma60)와 직접 대응되는 값만 써. "
        "KRW/USD나 퍼센트/가격을 섞어 쓰지 말고, 단위가 헷갈리거나 근거 필드가 불명확하면 숫자 대신 정성 표현으로 대체해. "
        "첫 문장은 이상한 숫자나 문맥 밖 숫자로 시작하지 마. "
        "첫 문장에서 해야 할 행동 방향은 분명히 말하되, 말머리 패턴은 매번 바꿔. "
        "첫 문장 시작이 반복되지 않게 '지금은', '현재 가격은', '현재 상황은', '지금 뭘 해야 하냐면' 같은 상투 표현은 피하고 자연스럽게 열어. "
        "wait/entry/추격주의/추가매수/hold/부분익절/손절 같은 의미 있는 행동 제안마다 이유를 바로 붙이고, 가능하면 한 문장 안에서 행동과 이유를 같이 말해. "
        "진입/추가매수 제안에는 가능하면 실행 비중(초기 진입 비중 + 확인 후 추가 계획)을 포함해서 안내해. "
        "부분익절 제안에는 가능하면 1차 청산 비율과 잔여 물량 운영 전략을 함께 넣어. "
        "리스크 관리는 stop이나 비중 축소 조건을 구체적으로 밝히고, 모호한 표현으로 끝내지 마. "
        "수치는 억지로 만들지 말고, 데이터와 맥락상 자연스럽게 제시 가능한 경우에만 사용해. "
        "딱딱한 보고서 말투(예: 판단됩니다, 권장됩니다, 현명할 것 같아, 확신이 없는 상태에서)는 쓰지 말고, 실제 트레이더가 옆에서 말하듯 자연스러운 구어체로 써. "
        "행동 이유는 차트 근거(지지/저항·거래량·추세·손절 기준)와 매수/매도 심리를 함께 결합해서 설명해. "
        "모든 commentary에는 매수/매도 심리 설명이 들어가야 하고, 최소 1번이 아니라 행동 제안(대기/진입/추가매수/부분익절/손절/추격주의)마다 심리 이유를 각각 붙여야 해. 심리 설명이 없으면 답변은 불완전해. "
        "매수/매도 심리는 반드시 '왜 그런 매수/매도가 나오는지'를 설명하는 문장 형태로 써야 한다. "
        "심리를 따로 떼어 설명하지 말고, 행동 근거 그 자체로 붙여서 말해(예: '매수 심리가 약함' 같은 분리형 금지, '매수 확신이 약해 흔들리면 바로 매도가 쏟아질 수 있어서 지금은 대기'처럼 행동 결론과 한 문장으로 연결). "
        "금지 표현(라벨형): '매수 심리가 부족하다', '매도 심리가 나온다'처럼 주어·원인·결과 없는 단문. "
        "필수 표현(원인-결과형): 상황 + 참여자 행동 + 가격 영향이 한 문장 안에 들어가야 해(예: 급락 이후 반등 구간이라 위에서 물린 매도가 계속 나와 반등 탄력이 약해질 수 있다). "
        "심리 문장에는 반드시 누가 행동하는지와 왜 그렇게 행동하는지를 포함해(예: 물린 매도, 차익실현 매도, 불안 매도, 확신 부족한 매수). "
        "심리 설명은 행동 이유에 자연스럽게 붙여서 실전용으로 쓰고, 추상적이거나 학술적인 해설은 금지. "
        "사람 말투를 살려서 최소 1문장은 실제 트레이더가 말하듯 감정이 묻어나게 써(예: '여기서 무리하면 물릴 수 있어', '지금 들어가면 흔들릴 가능성 높아', '이건 그냥 칼 잡는 느낌이야'). "
        "문장 전체는 분석 리포트처럼 차갑게 쓰지 말고, 직관적이고 대화형 코칭 톤을 유지해. 교과서식 정의·분류·이론 설명은 줄여. "
        "용어는 한국 개인투자자가 실제로 자주 쓰는 쉬운 트레이딩 단어만 사용해(예: 거래량, 지지, 저항, 물량, 흐름, 압력, 반등). "
        "뜻이 어색하거나 업계에서 거의 안 쓰는 단어는 쓰지 말고, 확신이 없는 용어는 더 쉬운 일상 표현으로 바꿔. "
        "문맥에 맞지 않는 오용·오타·억지 조어를 금지해(예: 호주량, 트레이딩 맥락의 폰트 같은 단어). "
        "대기라고 하면 왜 매수 주체가 아직 확신이 없는지와 어떤 매도 물량이 남아 있는지 설명하고, 진입이면 왜 매수 주체가 주도권을 잡는지, 손절이면 왜 공포/손절 연쇄가 커지는지, 익절이면 왜 차익실현·상단 매물이 나오는지까지 꼭 밝혀. "
        "입력의 supportBroken이 true면 broken support를 현재 지지처럼 말하지 말고, reclaimLevel을 회복해야 하는 되돌림 저항으로 해석해. "
        "supportBroken이 true일 땐 activeSupport를 현재 유효 지지로 쓰고, supportBroken이 false일 때만 support를 일반 지지처럼 써. "
        "입력의 resistanceBroken이 true면 breakoutLevel은 이미 돌파된 자리로 보고, 현재 저항처럼 부르지 마. "
        "resistanceBroken이 true일 땐 breakoutLevel을 눌림 지지/리테스트 기준으로 해석하고, 위쪽 저항은 activeResistance로 설명해. "
        "resistanceBroken이 false일 때만 resistance 또는 activeResistance를 현재 상단 저항으로 써. "
        "입력의 trendState가 sharp_drop이면 방어를 최우선으로 보고, 지지 근처라는 이유만으로 매수 제안을 하지 마. "
        "sharp_drop에서는 반등 확인, 지지 안정, 거래량 회복 같은 확인 신호가 있을 때만 진입을 제한적으로 허용해. "
        "sharp_drop + holder면 손절/비중축소 같은 자금보호 기준을 먼저 제시하고, sharp_drop + viewer면 기본값을 관망으로 둬. "
        "mode가 holder일 때는 신규 진입 대기 코칭을 하지 말고, 기존 포지션 관리(유지/추가대응/부분익절/비중축소/손절/방어)에 집중해. "
        "mode가 viewer일 때는 보유 물량 관리보다 진입 타이밍(눌림 진입 vs 돌파 진입), 추격 회피, 초기 비중 설계에 집중해. "
        "내부 변수명이나 영어 필드명(예: sharp_drop, activeSupport, reclaimLevel, breakoutLevel, trendState)은 절대 그대로 노출하지 마. "
        "보고서체, 설명체, 체크리스트 말투 금지. 정의하듯 말하지 말고 차트를 같이 보는 대화처럼 말해. "
        "투자 성향 이름(예: 보수형/수익보호형 같은 라벨)을 문장에 드러내지 말고, 판단 기울기만 자연스럽게 녹여. "
        "불릿/번호/제목/코드펜스/부가 텍스트 금지. "
        f"{behavior_prompt} {style_behavior_prompt}"
    )


def generate_ai_opinion(
    ticker: str,
    analysis: Dict[str, Any],
    personalization: Dict[str, Any],
) -> Dict[str, str]:
    started_at = time.perf_counter()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {
            "summary": "지금은 루나 해설 연결이 잠깐 끊겨 있어.",
            "commentary": "AI 키가 아직 연결되지 않아서 자동 해설이 비어 있어. 키만 연결되면 같은 데이터로 바로 다시 풀어줄게.",
        }

    summary = analysis["summary"]
    has_position = personalization["hasPosition"]
    style = personalization.get("style", "conservative")
    system_prompt = _build_system_prompt(has_position, style)

    compact_payload = {
        "ticker": ticker.upper(),
        "price": summary["currentPrice"],
        "prevClose": summary["prevClose"],
        "changePercent": summary["changePercent"],
        "dailyRangePercent": summary["dailyRangePercent"],
        "recentMovePercent5": summary["recentMovePercent5"],
        "trendState": summary["trendState"],
        "mode": "holder" if has_position else "viewer",
        "style": style,
        "state": summary["state"],
        "support": summary["support"],
        "supportBroken": summary.get("supportBroken", False),
        "activeSupport": summary.get("activeSupport", summary["support"]),
        "reclaimLevel": summary.get("reclaimLevel"),
        "supportRole": summary.get("supportRole", "active_support"),
        "resistance": summary["resistance"],
        "resistanceBroken": summary.get("resistanceBroken", False),
        "activeResistance": summary.get("activeResistance", summary["resistance"]),
        "breakoutLevel": summary.get("breakoutLevel"),
        "resistanceRole": summary.get("resistanceRole", "active_resistance"),
        "addBuyZone": personalization["suggestedAddBuyZone"],
        "stopLine": personalization["suggestedStop"],
        "takeProfit": personalization["suggestedTakeProfit"],
        "volumeRatio": summary["volumeRatio"],
        "ma20": summary["ma20"],
        "ma60": summary["ma60"],
        "pnlPercent": personalization["pnlPercent"],
    }
    user_prompt = f"입력 데이터(JSON): {json.dumps(compact_payload, ensure_ascii=False)}"

    try:
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model="gpt-4o-mini",
            instructions=system_prompt,
            input=user_prompt,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "luna_commentary",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "summary": {"type": "string"},
                            "commentary": {"type": "string"},
                        },
                        "required": ["summary", "commentary"],
                        "additionalProperties": False,
                    },
                    "strict": True,
                }
            },
            max_output_tokens=700,
            timeout=httpx.Timeout(40.0, connect=5.0, read=35.0, write=10.0),
        )

        raw_content = getattr(response, "output_text", "")
        content = str(raw_content or "").strip()
        content_length = len(content)
        logger.warning(
            "AI opinion raw response debug: type=%s empty=%s repr=%s",
            type(raw_content).__name__,
            not bool(content),
            _preview_text(repr(raw_content), limit=600),
        )
        if hasattr(response, "model_dump"):
            logger.warning(
                "AI opinion response shape=%s",
                _preview_text(repr(response.model_dump()), limit=600),
            )
        logger.warning(
            "AI opinion raw response received: length=%d preview=%s",
            content_length,
            _preview_text(content),
        )

        parsed = _safe_json_parse(content)
        parse_succeeded = parsed is not None
        normalization_failed = False
        forbidden_tone_failed = False

        if parsed:
            normalized, normalize_reason = _normalize_ai_opinion_payload(parsed)
            if normalized:
                elapsed = time.perf_counter() - started_at
                logger.info("AI opinion generation succeeded in %.3fs", elapsed)
                return normalized
            normalization_failed = True
            forbidden_tone_failed = normalize_reason == "forbidden_tone"

        logger.warning(
            "AI opinion post-process failed: parse_succeeded=%s normalization_failed=%s forbidden_tone_failed=%s",
            parse_succeeded,
            normalization_failed,
            forbidden_tone_failed,
        )
    except Exception as e:
        elapsed = time.perf_counter() - started_at
        logger.exception("AI opinion generation failed in %.3fs: %s", elapsed, e)

    elapsed = time.perf_counter() - started_at
    logger.warning("AI opinion fallback used after %.3fs", elapsed)
    return _fallback_ai_opinion(summary)


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


@app.get("/api/analyze")
async def analyze(
    ticker: str = Query(..., min_length=1),
    mode: str = Query("viewer"),
    avg_price: Optional[float] = Query(None),
    quantity: Optional[int] = Query(None),
    style: str = Query("conservative"),
) -> dict:
    try:
        if mode not in {"viewer", "holder"}:
            raise ValueError("mode는 viewer 또는 holder 여야 해")

        if style not in STYLE_GUIDE:
            raise ValueError("지원하지 않는 투자성향이야")

        if mode == "holder":
            if avg_price is None or quantity is None:
                raise ValueError("보유자 모드에서는 평단가와 보유수량을 입력해야 해")

        instrument = resolve_instrument(ticker)
        logger.info(
            "Analyze request resolved ticker=%s symbol=%s market=%s provider=%s",
            ticker,
            instrument.get("symbol"),
            instrument.get("market"),
            instrument.get("provider"),
        )
        prices = await fetch_prices_for_instrument(instrument)
        analysis = build_analysis(prices)
        realtime_meta = select_realtime_quote(instrument["symbol"])
        realtime_quote = realtime_meta.get("quote")
        if realtime_quote:
            analysis["summary"] = recalculate_summary_for_current_price(
                analysis["summary"],
                float(realtime_quote["price"]),
            )
        analysis["summary"]["currentPriceSource"] = realtime_meta["currentPriceSource"]
        analysis["summary"]["currentPriceTimestamp"] = realtime_meta["currentPriceTimestamp"]
        analysis["summary"]["realtimeApplied"] = realtime_meta["realtimeApplied"]
        analysis["summary"]["realtimeStale"] = realtime_meta["realtimeStale"]

        personalization = build_personalization(
            mode=mode,
            current_price=analysis["summary"]["currentPrice"],
            support=analysis["summary"]["support"],
            resistance=analysis["summary"]["resistance"],
            avg_price=avg_price,
            quantity=quantity,
            style=style,
        )
        ai_opinion = generate_ai_opinion(instrument["symbol"], analysis, personalization)
        if (
            not ai_opinion
            or not isinstance(ai_opinion, dict)
            or not str(ai_opinion.get("summary", "")).strip()
            or not str(ai_opinion.get("commentary", "")).strip()
        ):
            ai_opinion = _fallback_ai_opinion(analysis["summary"])

        analysis["explanation"] = analysis["trendSummary"]
        analysis["lessons"] = []

        return {
            "ticker": instrument["symbol"],
            "instrument": instrument,
            "analysis": analysis,
            "personalization": personalization,
            "stateHint": build_state_hint(
                summary=analysis["summary"],
                has_position=personalization["hasPosition"],
                avg_price=personalization["avgPrice"],
                style=personalization["style"],
            ),
            "aiOpinion": ai_opinion,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 중 오류가 발생했어: {e}")
