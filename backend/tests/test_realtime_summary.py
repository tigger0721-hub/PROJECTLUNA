from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.legacy_api import app
from app.legacy_api import recalculate_summary_for_current_price, select_realtime_quote


def _iso_seconds_ago(seconds_ago: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(seconds=seconds_ago)).isoformat().replace("+00:00", "Z")


def test_realtime_quote_applied_recalculates_summary_consistently() -> None:
    summary = {
        "currentPrice": 100.0,
        "prevClose": 95.0,
        "changePercent": 5.26,
        "dayHigh": 102.0,
        "dayLow": 98.0,
        "dailyRangePercent": 4.0,
        "recentMovePercent5": 2.04,
        "ma20": 97.0,
        "support": 96.0,
        "resistance": 110.0,
    }
    cache = {"NVDA": {"price": 105.0, "received_at": _iso_seconds_ago(2)}}

    realtime = select_realtime_quote("NVDA", quote_cache=cache)
    assert realtime["realtimeApplied"] is True
    assert realtime["realtimeStale"] is False
    assert realtime["currentPriceSource"] == "kis_realtime"

    updated = recalculate_summary_for_current_price(summary, realtime["quote"]["price"])
    assert updated["currentPrice"] == 105.0
    assert updated["prevClose"] == 95.0
    assert updated["changePercent"] == 10.53
    assert updated["dailyRangePercent"] == 3.81
    assert updated["trendState"] == "sharp_rise"


def test_stale_realtime_quote_falls_back_to_historical() -> None:
    cache = {"NVDA": {"price": 105.0, "received_at": _iso_seconds_ago(7)}}
    realtime = select_realtime_quote("NVDA", quote_cache=cache)

    assert realtime["quote"] is None
    assert realtime["realtimeApplied"] is False
    assert realtime["realtimeStale"] is True
    assert realtime["currentPriceSource"] == "historical_fallback"
    assert realtime["currentPriceTimestamp"] is not None


def test_missing_realtime_quote_falls_back_to_historical() -> None:
    realtime = select_realtime_quote("NVDA", quote_cache={})

    assert realtime["quote"] is None
    assert realtime["realtimeApplied"] is False
    assert realtime["realtimeStale"] is False
    assert realtime["currentPriceSource"] == "historical_fallback"
    assert realtime["currentPriceTimestamp"] is None


def test_analyze_response_includes_realtime_flags_for_fallback(monkeypatch) -> None:
    async def fake_fetch_prices(_instrument):
        return [{"time": "2026-03-26", "open": 100, "high": 102, "low": 98, "close": 101, "volume": 1000}] * 130

    def fake_build_analysis(_prices):
        return {
            "summary": {
                "currentPrice": 101.0,
                "prevClose": 100.0,
                "changePercent": 1.0,
                "dayHigh": 102.0,
                "dayLow": 98.0,
                "dailyRangePercent": 3.96,
                "recentMovePercent5": 2.0,
                "ma20": 99.0,
                "support": 95.0,
                "resistance": 110.0,
                "activeSupport": 95.0,
                "activeResistance": 110.0,
                "state": "박스권",
                "trendState": "normal",
                "volumeRatio": 1.0,
            },
            "trendSummary": "ok",
            "volumeSummary": "ok",
            "supportCandidates": [],
            "resistanceCandidates": [],
            "chart": {"candles": [], "ma5": [], "ma20": [], "ma60": [], "ma120": [], "volume": []},
        }

    monkeypatch.setattr("app.legacy_api.resolve_instrument", lambda ticker: {"symbol": ticker, "country": "US"})
    monkeypatch.setattr("app.legacy_api.fetch_prices_for_instrument", fake_fetch_prices)
    monkeypatch.setattr("app.legacy_api.build_analysis", fake_build_analysis)
    monkeypatch.setattr("app.legacy_api.generate_ai_opinion", lambda *_args, **_kwargs: {"summary": "s", "commentary": "c"})

    client = TestClient(app)
    response = client.get("/api/analyze", params={"ticker": "NVDA"})
    assert response.status_code == 200
    summary = response.json()["analysis"]["summary"]

    assert summary["currentPriceSource"] == "historical_fallback"
    assert summary["realtimeApplied"] is False
    assert summary["realtimeStale"] is False
