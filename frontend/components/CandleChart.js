"use client";

import { useEffect, useMemo, useRef } from "react";
import { createChart } from "lightweight-charts";
import { formatNumber, formatVolume } from "@/utils/formatPrice";

export default function CandleChart({ chartData, support, resistance, country }) {
  const containerRef = useRef(null);
  const chartRef = useRef(null);

  const latestVolume = useMemo(() => {
    const volumeData = chartData?.volume || [];
    if (!volumeData.length) return null;

    for (let i = volumeData.length - 1; i >= 0; i -= 1) {
      const value = volumeData[i]?.value;
      if (value !== null && value !== undefined) return value;
    }

    return null;
  }, [chartData]);

  const latestVolumeLabel = latestVolume === null ? null : formatVolume(latestVolume, country);

  useEffect(() => {
    if (!containerRef.current || !chartData) return;

    const precision = country === "US" ? 2 : 0;
    const minMove = country === "US" ? 0.01 : 1;

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height: 460,
      layout: {
        background: { color: "#020617" },
        textColor: "#cbd5e1"
      },
      grid: {
        vertLines: { color: "rgba(51,65,85,0.35)" },
        horzLines: { color: "rgba(51,65,85,0.35)" }
      },
      rightPriceScale: {
        borderColor: "#334155",
        scaleMargins: {
          top: 0.08,
          bottom: 0.28
        }
      },
      timeScale: {
        borderColor: "#334155",
        timeVisible: true,
        rightOffset: 6,
        barSpacing: 9,
        minBarSpacing: 6
      },
      crosshair: {
        mode: 1
      },
      localization: {
        priceFormatter: (price) => formatNumber(price, country)
      }
    });

    chartRef.current = chart;

    const candleSeries = chart.addCandlestickSeries({
      priceFormat: {
        type: "price",
        precision,
        minMove
      },
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderVisible: false,
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
      priceLineVisible: true
    });

    const ma5Series = chart.addLineSeries({
      priceFormat: {
        type: "price",
        precision,
        minMove
      },
      color: "#f59e0b",
      lineWidth: 2,
      priceLineVisible: false
    });

    const ma20Series = chart.addLineSeries({
      priceFormat: {
        type: "price",
        precision,
        minMove
      },
      color: "#60a5fa",
      lineWidth: 2,
      priceLineVisible: false
    });

    const ma60Series = chart.addLineSeries({
      priceFormat: {
        type: "price",
        precision,
        minMove
      },
      color: "#a78bfa",
      lineWidth: 2,
      priceLineVisible: false
    });

    const volumeSeries = chart.addHistogramSeries({
      priceFormat: {
        type: "custom",
        formatter: (value) => formatVolume(value, country)
      },
      priceScaleId: "",
      priceLineVisible: false,
      lastValueVisible: false,
      scaleMargins: {
        top: 0.78,
        bottom: 0
      }
    });

    candleSeries.setData(chartData.candles || []);
    ma5Series.setData(chartData.ma5 || []);
    ma20Series.setData(chartData.ma20 || []);
    ma60Series.setData(chartData.ma60 || []);
    volumeSeries.setData(chartData.volume || []);

    if (support) {
      candleSeries.createPriceLine({
        price: support,
        color: "#22c55e",
        lineWidth: 1,
        lineStyle: 2,
        axisLabelVisible: true,
        title: "지지"
      });
    }

    if (resistance) {
      candleSeries.createPriceLine({
        price: resistance,
        color: "#ef4444",
        lineWidth: 1,
        lineStyle: 2,
        axisLabelVisible: true,
        title: "저항"
      });
    }

    const fit = () => {
      chart.applyOptions({
        width: containerRef.current ? containerRef.current.clientWidth : 320
      });
      chart.timeScale().fitContent();
    };

    fit();

    let resizeTimer = null;

    const handleResize = () => {
      if (resizeTimer) clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => {
        fit();
      }, 120);
    };

    window.addEventListener("resize", handleResize);
    window.addEventListener("orientationchange", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      window.removeEventListener("orientationchange", handleResize);
      if (resizeTimer) clearTimeout(resizeTimer);
      chart.remove();
      chartRef.current = null;
    };
  }, [chartData, country, support, resistance]);

  return (
    <div style={{ position: "relative", width: "100%", minHeight: 460 }}>
      <div ref={containerRef} style={{ width: "100%", minHeight: 460 }} />
      {latestVolumeLabel && (
        <div
          style={{
            position: "absolute",
            right: 12,
            bottom: 34,
            zIndex: 10,
            fontSize: 12,
            lineHeight: 1.2,
            color: "#cbd5e1",
            background: "rgba(15, 23, 42, 0.9)",
            border: "1px solid rgba(71, 85, 105, 0.7)",
            borderRadius: 6,
            padding: "4px 8px",
            pointerEvents: "none"
          }}
        >
          {latestVolumeLabel}
        </div>
      )}
    </div>
  );
}
