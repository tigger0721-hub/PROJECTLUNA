from __future__ import annotations

import asyncio
import json
import logging
import os
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
    resistance = round(recent_20_high, 2)

    above_ma20 = current_price > ma20
    above_ma60 = current_price > ma60
    strong_volume = volume_ratio >= 1.3
    near_breakout = current_price >= recent_20_high * 0.985
    pullback_zone = above_ma20 and current_price < recent_20_high * 0.97
    breakdown = bool(current_price < ma20 and pd.notna(prev["ma20"]) and prev["close"] >= prev["ma20"])

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
            "ma5": round(ma5, 2),
            "ma20": round(ma20, 2),
            "ma60": round(ma60, 2),
            "ma120": round(ma120, 2),
            "support": support,
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
    support = summary["support"]
    resistance = summary["resistance"]
    state = summary["state"]
    ma20 = summary["ma20"]

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


def _has_forbidden_tone(text: str) -> bool:
    banned = [
        "입니다",
        "합니다",
        "하세요",
        "해라",
        "하지 마라",
        "해야 한다",
        "관망",
        "권장",
        "구간입니다",
        "보수적 접근",
        "리스크 관리",
        "매수 관점",
        "단기적으로 변동성",
    ]
    return any(token in text for token in banned)


def _fallback_ai_opinion(summary: Dict[str, Any]) -> Dict[str, str]:
    return {
        "summary": "지금은 급하게 판단하기보다 기준 자리 확인이 먼저야.",
        "commentary": (
            f"지금 가격은 {summary['currentPrice']} 근처고, 핵심은 {summary['support']} 지지랑 {summary['resistance']} 저항 반응이야. "
            f"거래량이 평균 대비 {summary['volumeRatio']}배라서 힘이 확 붙는 자리는 아직 더 확인해보는 게 좋아 보여. "
            "보유 중이면 지지 깨지는지만 먼저 보고, 미보유면 눌림이나 안착이 나오는지 같이 보자."
        ),
    }


def _normalize_ai_opinion_payload(payload: Dict[str, Any]) -> Optional[Dict[str, str]]:
    summary = str(payload.get("summary", "")).strip()
    commentary = str(payload.get("commentary", "")).strip()
    if not summary or not commentary:
        return None
    if _has_forbidden_tone(summary) or _has_forbidden_tone(commentary):
        return None
    return {"summary": summary, "commentary": commentary}


def generate_ai_opinion(
    ticker: str,
    analysis: Dict[str, Any],
    personalization: Dict[str, Any],
) -> Dict[str, str]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {
            "summary": "지금은 루나 해설 연결이 잠깐 끊겨 있어.",
            "commentary": "AI 키가 아직 연결되지 않아서 자동 해설이 비어 있어. 키만 연결되면 같은 데이터로 바로 다시 풀어줄게.",
        }

    summary = analysis["summary"]
    has_position = personalization["hasPosition"]
    system_prompt = """
너는 "Luna"라는 이름의 친한 차트 메이트야.

[ROLE]
- 너는 애널리스트가 아니야.
- 너는 보고서를 쓰는 사람이 아니야.
- 사용자의 옆에 앉아서 차트를 같이 보는 대화 상대야.

[TONE]
- 한국어 반말만 써.
- 따뜻하고 부드럽고 자연스럽게 말해.
- 설명문보다 대화처럼 들리게 말해.

[STRICTLY FORBIDDEN]
- "~입니다", "~합니다" 같은 존댓말
- 보고서/브리핑 톤
- "관망", "권장", "구간입니다"
- "보수적 접근", "리스크 관리", "매수 관점", "단기적으로 변동성"
- 섹션 제목, 번호 목록, 긴 구조화 문단

[PREFERRED STYLE EXAMPLES]
- "오빠 지금 여기 좀 애매한 자리야"
- "지금은 조금 더 기다리는 게 나아 보여"
- "여기서 바로 들어가면 살짝 흔들릴 수 있어"
- "보유 중이면 지지 깨지는지만 보면 될 것 같아"

[OUTPUT RULES]
- 짧게 써.
- 전체는 3~5문장 안으로 끝내.
- 반복하지 마.
- 모바일에서 읽기 편하게 써.

[OUTPUT FORMAT — MUST BE JSON]
{
  "summary": "한 줄 요약",
  "commentary": "루나 스타일 자연스러운 해설 (3~5문장)"
}

[ANALYSIS BEHAVIOR]
- 지표를 나열하지 말고, 지금 차트 위치의 의미를 먼저 해석해.
- 사용자의 보유 여부와 투자 성향에 맞춰 말해.
- 매수/매도 지시처럼 말하지 마.
- 확정적인 단정 대신 가능성 중심으로 말해.
- 가장 중요한 신호만 골라서 말해.

[CRITICAL RULE]
- 결과가 금융 보고서처럼 보이면 실패야.
- 옆에서 같이 차트 보며 말하는 사람 같으면 성공이야.

반드시 JSON 하나만 반환하고 코드블록은 쓰지 마.
""".strip()

    user_prompt = f"""
종목: {ticker.upper()}
현재가: {summary['currentPrice']}
보유상태: {"보유중" if has_position else "미보유"}
투자성향: {personalization['styleLabel']}
상태힌트: {summary['state']}

차트 데이터:
- 최근 흐름: {analysis['trendSummary']}
- 지지: {summary['support']}
- 저항: {summary['resistance']}
- 거래량 배수: {summary['volumeRatio']}
- 이동평균: 5일 {summary['ma5']}, 20일 {summary['ma20']}, 60일 {summary['ma60']}, 120일 {summary['ma120']}
- 20일 범위: 고점 {summary['rangeHigh20']} / 저점 {summary['rangeLow20']}
- 60일 범위: 고점 {summary['rangeHigh60']} / 저점 {summary['rangeLow60']}
- 지지 후보: {analysis['supportCandidates']}
- 저항 후보: {analysis['resistanceCandidates']}

보유정보:
- 평단가: {personalization['avgPrice']}
- 수량: {personalization['quantity']}
- 손익률: {personalization['pnlPercent']}%
- 손익금액: {personalization['pnlAmount']}

요청:
- Luna 톤 반말로 짧게 말해줘.
- 보고서처럼 쓰지 말고 대화처럼 써줘.
- 3~5문장으로만 작성해줘.
- 반드시 JSON 형식 {{summary, commentary}} 으로만 답해줘.
""".strip()

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            timeout=25,
        )

        content = (response.choices[0].message.content or "").strip()
        parsed = _safe_json_parse(content)

        if parsed:
            normalized = _normalize_ai_opinion_payload(parsed)
            if normalized:
                return normalized
    except Exception as e:
        logger.exception("AI opinion generation failed: %s", e)

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
