from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _extract_series(points: List[Dict[str, Any]]) -> List[Optional[float]]:
    extracted: List[Optional[float]] = []
    for point in points:
        value = point.get("value")
        try:
            extracted.append(float(value))
        except (TypeError, ValueError):
            extracted.append(None)
    return extracted


def render_analysis_chart_image(analysis: Dict[str, Any], window: int = 65) -> Optional[Path]:
    chart = analysis.get("chart")
    summary = analysis.get("summary")
    if not isinstance(chart, dict) or not isinstance(summary, dict):
        return None

    candles = chart.get("candles")
    if not isinstance(candles, list) or not candles:
        return None

    visible_candles = candles[-window:]
    x = list(range(len(visible_candles)))

    close_values: List[float] = []
    for candle in visible_candles:
        try:
            close_values.append(float(candle["close"]))
        except (TypeError, ValueError, KeyError):
            close_values.append(float("nan"))

    ma5_series = _extract_series(chart.get("ma5", [])[-len(visible_candles):])
    ma20_series = _extract_series(chart.get("ma20", [])[-len(visible_candles):])
    ma60_series = _extract_series(chart.get("ma60", [])[-len(visible_candles):])

    fig, ax = plt.subplots(figsize=(8.2, 3.8), dpi=140)
    ax.set_facecolor("#0f172a")
    fig.patch.set_facecolor("#0f172a")

    ax.plot(x, close_values, color="#e2e8f0", linewidth=1.3, label="Close")
    if ma5_series:
        ax.plot(x, ma5_series, color="#f59e0b", linewidth=1.1, label="MA5")
    if ma20_series:
        ax.plot(x, ma20_series, color="#22d3ee", linewidth=1.1, label="MA20")
    if ma60_series:
        ax.plot(x, ma60_series, color="#a78bfa", linewidth=1.1, label="MA60")

    support = summary.get("activeSupport", summary.get("support"))
    resistance = summary.get("activeResistance", summary.get("resistance"))
    try:
        ax.axhline(float(support), color="#34d399", linestyle="--", linewidth=1.0, alpha=0.9, label="Support")
    except (TypeError, ValueError):
        pass
    try:
        ax.axhline(float(resistance), color="#f87171", linestyle="--", linewidth=1.0, alpha=0.9, label="Resistance")
    except (TypeError, ValueError):
        pass

    ax.grid(color="#334155", alpha=0.35, linestyle="-", linewidth=0.6)
    ax.tick_params(colors="#cbd5e1", labelsize=8)
    ax.spines["bottom"].set_color("#475569")
    ax.spines["left"].set_color("#475569")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xlim(0, max(len(x) - 1, 1))
    ax.set_xticks([])
    ax.set_title("Recent price window (AI hint)", color="#e2e8f0", fontsize=9)

    legend = ax.legend(loc="upper left", fontsize=7, framealpha=0.2)
    if legend:
        for text in legend.get_texts():
            text.set_color("#e2e8f0")

    output = Path(tempfile.NamedTemporaryFile(prefix="luna_chart_", suffix=".png", delete=False).name)
    fig.tight_layout()
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)
    return output
