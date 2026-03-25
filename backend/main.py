from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from io import StringIO
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
logger = logging.getLogger(__name__)

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

    resistance_pool = sorted(
        {
            round(recent_20_high, 2),
            round(recent_60_high, 2),
            round(ma20, 2),
            round(ma60, 2),
            round(ma120, 2),
            *( [reclaim_level] if reclaim_level is not None else [] ),
        }
    )
    upside_resistance = [level for level in resistance_pool if level >= current_price * 1.005]
    resistance = round(min(upside_resistance), 2) if upside_resistance else round(max(resistance_pool), 2)

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
    resistance = summary["resistance"]
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

    if trend_state == "sharp_drop":
        if support_broken and reclaim_level is not None:
            return {
                "summary": "지금은 급락에 기존 지지까지 이탈해서 방어 기준이 더 중요해.",
                "commentary": (
                    f"{reclaim_level}은 원래 지지였는데 이미 깨져서 지금은 되돌림 저항처럼 보는 게 맞아. "
                    f"반등이 나와도 {reclaim_level} 회복 전엔 성급히 들어가지 말고, 아래에선 {active_support} 반응 확인이 먼저야. "
                    f"보유 중이면 {active_support}까지 밀릴 때 손실 커질 수 있어서 비중부터 관리하자."
                ),
            }
        return {
            "summary": "지금은 급락 구간이라 수익보다 방어 확인이 먼저야.",
            "commentary": (
                f"오늘 {summary.get('changePercent', 0)}% 밀린 급락 흐름이라 지지 근처라도 성급한 진입은 위험해. "
                f"{active_support} 지지에서 반등이 붙고 거래량이 살아나는지 확인되기 전엔 기다리는 게 좋아. "
                f"보유 중이면 {active_support} 이탈 시 손실 확대로 이어질 수 있어서 비중 줄일 기준부터 먼저 잡자."
            ),
        }
    if support_broken and reclaim_level is not None:
        return {
            "summary": "기존 지지는 이미 깨져서 지금은 회복 여부를 먼저 봐야 해.",
            "commentary": (
                f"{reclaim_level}은 원래 지지였지만 지금은 되돌림 저항에 가까워서 회복 전엔 공격적으로 보기 어려워. "
                f"아래에선 {active_support}이 다음 지지 후보라 그 자리 반응이 확인될 때까지 분할 대응이 좋아. "
                "급하게 추격하지 말고 회복 캔들이랑 거래량 붙는지부터 같이 보자."
            ),
        }
    return {
        "summary": "지금은 급하게 판단하기보다 기준 자리 확인이 먼저야.",
        "commentary": (
            f"지금 가격은 {summary['currentPrice']} 근처고, 핵심은 {active_support} 지지랑 {summary['resistance']} 저항 반응이야. "
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
            "유지/추가매수/부분익절/손절 판단은 꼭 담되 항목처럼 나열하지 말고 한 흐름 안에서 연결하고, 가능하면 한 문장 안에서 행동과 이유를 같이 말해줘. "
            "수익 구간이면 수익 보호와 분할익절을 자연스럽게 넣고, 손실·약세 구간이면 지지 지키는지와 이탈 시 정리 기준을 먼저 챙겨줘. "
            "addBuyZone, takeProfit, stopLine, support/resistance 가격 기준을 말에 녹여서 '여기선~ 대신 ~깨지면~' 같은 대화체로 풀고, 이유는 지지/저항·거래량·추세·손절 기준 같은 차트 근거로 붙여줘. "
            "가능하면 hold 관점 + 추가 조건 + 매도 또는 stop 기준을 함께 담고, 마지막은 짧게 멘탈 케어 한마디로 마무리해."
        )
    return (
        "미보유자 기준으로 써. 지금이 대기인지 진입 가능한지부터 분명하게 말하되, 설명문처럼 정의하지 말고 친구가 옆에서 코칭하듯 말해줘. "
        "wait vs entry 판단은 꼭 보여주고, 언제 들어갈지는 눌림 가격대나 돌파 안착 조건으로 구체적으로 말해줘. "
        "눌림이면 '어느 근처에서 반응 나오면 들어간다', 돌파면 '어느 저항 위 안착 확인 후 따라간다'처럼 실전 문장으로 이어줘. "
        "지금 추격이 위험한 자리면 바로 따라붙지 말라고 자연스럽게 경고하고, 가능하면 한 문장 안에서 행동과 이유를 같이 말해줘. "
        "이유는 지지/저항·거래량·추세·손절 기준 같은 차트 근거로 짧고 또렷하게 붙여줘. "
        "문장은 2~4문장 안에서 살아있는 대화체로, 체크리스트처럼 끊지 말고 흐름 있게 써줘. "
        "마지막엔 한 줄 정도 편하게 멘탈 케어를 섞어."
    )


def _build_system_prompt(has_position: bool, style: str) -> str:
    behavior_prompt = _build_mode_behavior_prompt(has_position)
    style_behavior_prompt = _build_style_behavior_prompt(style, has_position)
    return (
        "너는 Luna. 한국어 반말의 친근한 트레이딩 메이트 톤으로만 답해. "
        "반드시 JSON 객체 하나만 출력: {\"summary\":\"\", \"commentary\":\"\"}. "
        "summary는 1문장, commentary는 2~4문장으로 짧고 실전 행동 중심으로 써. "
        "wait/entry/추격주의/추가매수/hold/부분익절/손절 같은 의미 있는 행동 제안마다 이유를 바로 붙이고, 가능하면 한 문장 안에서 행동과 이유를 같이 말해. "
        "행동과 이유를 멀리 떼어놓지 말고, 이유는 지지/저항·거래량·추세·손절 기준 같은 차트 근거로 써. "
        "입력의 supportBroken이 true면 broken support를 현재 지지처럼 말하지 말고, reclaimLevel을 회복해야 하는 되돌림 저항으로 해석해. "
        "supportBroken이 true일 땐 activeSupport를 현재 유효 지지로 쓰고, supportBroken이 false일 때만 support를 일반 지지처럼 써. "
        "입력의 trendState가 sharp_drop이면 방어를 최우선으로 보고, 지지 근처라는 이유만으로 매수 제안을 하지 마. "
        "sharp_drop에서는 반등 확인, 지지 안정, 거래량 회복 같은 확인 신호가 있을 때만 진입을 제한적으로 허용해. "
        "sharp_drop + holder면 손절/비중축소 같은 자금보호 기준을 먼저 제시하고, sharp_drop + viewer면 기본값을 관망으로 둬. "
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

        prices = await fetch_daily_prices(ticker)
        analysis = build_analysis(prices)
        personalization = build_personalization(
            mode=mode,
            current_price=analysis["summary"]["currentPrice"],
            support=analysis["summary"]["support"],
            resistance=analysis["summary"]["resistance"],
            avg_price=avg_price,
            quantity=quantity,
            style=style,
        )
        ai_opinion = generate_ai_opinion(ticker, analysis, personalization)
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
            "ticker": ticker.upper(),
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
