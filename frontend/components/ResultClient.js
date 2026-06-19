"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import CandleChart from "@/components/CandleChart";
import DecisionCard from "@/components/DecisionCard";
import { formatNumber, formatPrice, formatPriceText } from "@/utils/formatPrice";

const pageStyle = {
  minHeight: "100vh",
  background: "#0B0F14",
  color: "#F3F6FA",
  padding: "16px 12px 96px"
};

const wrapperStyle = {
  maxWidth: 1100,
  margin: "0 auto"
};

const cardStyle = {
  background: "#121821",
  border: "1px solid #263241",
  borderRadius: 24,
  padding: 18,
  boxShadow: "0 10px 24px rgba(0,0,0,0.22)",
  color: "#F3F6FA"
};

const chipStyle = {
  display: "inline-flex",
  alignItems: "center",
  gap: 6,
  borderRadius: 999,
  background: "#171F2A",
  border: "1px solid #263241",
  color: "#F3F6FA",
  fontSize: 13,
  padding: "8px 12px"
};

const summaryCardStyle = {
  background: "#171F2A",
  borderRadius: 18,
  border: "1px solid #263241",
  padding: 14
};

const viewerFallback = {
  headline: "지금은 확인이 먼저입니다.",
  reasonSummary: "현재 데이터만으로는 진입 타이밍을 단정하기 어렵습니다.",
  actions: ["신규 진입은 보류하고 지지/저항 반응을 확인하세요.", "추격하지 말고 다음 확인 구간을 기다리세요."],
  recheckConditions: ["지지선 반등", "저항 돌파 후 안착", "거래량 회복"]
};

const holderFallback = {
  headline: "보유 기준을 다시 확인하세요.",
  reasonSummary: "현재 데이터만으로는 추가 매수보다 리스크 관리가 우선입니다.",
  actions: ["손절/보호 기준을 확인하고 무리한 추가 매수는 피하세요.", "추가매수는 조건 충족 전 보류하세요."],
  recheckConditions: ["평단 대비 손익 변화", "지지선 이탈", "저항 돌파 후 안착"]
};

function LoadingView() {
  const lunaImages = useMemo(
    () => [
      "/images/luna/luna_idle.png",
      "/images/luna/luna_thinking.png",
      "/images/luna/luna_happy.png"
    ],
    []
  );

  const messages = useMemo(
    () => [
      "오빠, 루나가 차트 흐름 먼저 보고 있어.",
      "지지선이랑 저항선 위치를 같이 확인중이야.",
      "지금 거래량이랑 추세도 같이 읽어보는 중이야.",
      "매수 타이밍이 자연스러운 자리인지 보고 있어.",
      "추격이 괜찮은지, 눌림이 나은지도 같이 체크중이야.",
      "보유자 기준 대응이 더 나은지 같이 정리하고 있어."
    ],
    []
  );

  const [dots, setDots] = useState("");
  const [messageIndex, setMessageIndex] = useState(0);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [imagesPreloaded, setImagesPreloaded] = useState(false);

  useEffect(() => {
    const dotsInterval = setInterval(() => {
      setDots((prev) => (prev.length >= 3 ? "" : prev + "."));
    }, 500);

    const messageInterval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % messages.length);
    }, 1800);

    return () => {
      clearInterval(dotsInterval);
      clearInterval(messageInterval);
    };
  }, [messages]);

  useEffect(() => {
    let active = true;

    const preloadImages = async () => {
      await Promise.all(
        lunaImages.map(
          (src) =>
            new Promise((resolve) => {
              const image = new window.Image();
              image.src = src;

              if (image.complete) {
                resolve();
                return;
              }

              image.onload = resolve;
              image.onerror = resolve;
            })
        )
      );

      if (active) {
        setImagesPreloaded(true);
      }
    };

    preloadImages();

    return () => {
      active = false;
    };
  }, [lunaImages]);

  useEffect(() => {
    if (!imagesPreloaded) return undefined;

    const imageInterval = setInterval(() => {
      setCurrentImageIndex((prev) => (prev + 1) % lunaImages.length);
    }, 1200);

    return () => {
      clearInterval(imageInterval);
    };
  }, [imagesPreloaded, lunaImages]);

  return (
    <main style={pageStyle}>
      <div style={{ ...wrapperStyle, maxWidth: 720 }}>
        <div
          style={{
            ...cardStyle,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            textAlign: "center",
            padding: "40px 24px"
          }}
        >
          <div
            style={{
              marginBottom: 20,
              position: "relative",
              width: "min(160px, 42vw)",
              aspectRatio: "1 / 1"
            }}
          >
            {lunaImages.map((src, index) => (
              <img
                key={src}
                src={src}
                alt="루나 로딩 이미지"
                style={{
                  position: "absolute",
                  inset: 0,
                  width: "100%",
                  height: "100%",
                  objectFit: "contain",
                  borderRadius: 20,
                  display: "block",
                  opacity:
                    imagesPreloaded && currentImageIndex === index ? 1 : 0,
                  transition: "opacity 300ms ease"
                }}
              />
            ))}
          </div>

          <h1 style={{ margin: 0, fontSize: 28, lineHeight: 1.25 }}>
            루나가 차트 분석중{dots}
          </h1>

          <p
            style={{
              marginTop: 14,
              color: "#A7B0BD",
              fontSize: 17,
              lineHeight: 1.7,
              minHeight: 58
            }}
          >
            {messages[messageIndex]}
          </p>

          <div
            style={{
              marginTop: 20,
              width: "100%",
              height: 8,
              background: "#263241",
              borderRadius: 9999,
              overflow: "hidden",
              position: "relative"
            }}
          >
            <div className="loading-bar" />
          </div>

          <div style={{ marginTop: 16, color: "#A7B0BD", fontSize: 14 }}>
            오빠, 잠깐만 기다려줘. 루나가 보기 편하게 정리하고 있어.
          </div>
        </div>
      </div>

      <style jsx>{`
        .loading-bar {
          position: absolute;
          top: 0;
          left: 0;
          width: 35%;
          height: 100%;
          background: linear-gradient(90deg, #4DA3FF, #3DDC97);
          border-radius: 9999px;
          animation: loadingBar 1.5s infinite ease-in-out;
        }

        @keyframes loadingBar {
          0% { transform: translateX(-120%); }
          100% { transform: translateX(320%); }
        }

      `}</style>
    </main>
  );
}

function BottomSheet({ open, onClose, children }) {
  if (!open) return null;

  return (
    <>
      <div
        onClick={onClose}
        style={{
          position: "fixed",
          inset: 0,
          background: "rgba(2,6,23,0.65)",
          zIndex: 40
        }}
      />
      <div
        style={{
          position: "fixed",
          left: 0,
          right: 0,
          bottom: 0,
          zIndex: 50,
          background: "#121821",
          borderTopLeftRadius: 24,
          borderTopRightRadius: 24,
          border: "1px solid #263241",
          boxShadow: "0 -10px 30px rgba(0,0,0,0.35)",
          padding: "16px 16px 28px",
          maxHeight: "78vh",
          overflowY: "auto"
        }}
      >
        <div
          style={{
            width: 56,
            height: 6,
            borderRadius: 999,
            background: "#263241",
            margin: "0 auto 16px"
          }}
        />
        {children}
      </div>
    </>
  );
}

function SummaryRow({ label, value }) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        gap: 12,
        padding: "10px 0",
        borderBottom: "1px solid rgba(167,176,189,0.2)"
      }}
    >
      <div style={{ color: "#A7B0BD", fontSize: 14 }}>{label}</div>
      <div style={{ color: "#F3F6FA", fontWeight: 700, textAlign: "right" }}>{value}</div>
    </div>
  );
}

function formatPriceOrDash(value, country) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  return formatPrice(value, country);
}

function formatNumberOrDash(value, country) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  return formatNumber(value, country);
}

function movingAverageText(summary, country) {
  const ma5 = formatPriceOrDash(summary?.ma5, country);
  const ma20 = formatPriceOrDash(summary?.ma20, country);
  const ma60 = formatPriceOrDash(summary?.ma60, country);
  const ma120 = formatPriceOrDash(summary?.ma120, country);
  return `5일 ${ma5} / 20일 ${ma20} / 60일 ${ma60} / 120일 ${ma120}`;
}

function toArray(value) {
  if (Array.isArray(value)) return value.filter(Boolean).map(String);
  if (typeof value === "string" && value.trim()) return [value.trim()];
  return [];
}

function detectUserMode(result, searchParams) {
  const rawMode = `${searchParams.get("mode") || result?.userMode || result?.mode || result?.personalization?.holderView || ""}`.toLowerCase();
  if (rawMode.includes("holder") || rawMode.includes("보유")) return "holder";
  return "viewer";
}

function detectZone(result) {
  const rawZone = `${result?.zone || result?.profitZone || result?.analysis?.zone || result?.analysis?.summary?.zone || ""}`.toLowerCase();
  if (rawZone.includes("profit") || rawZone.includes("수익")) return "profit";
  if (rawZone.includes("loss") || rawZone.includes("손실")) return "loss";
  if (rawZone.includes("neutral") || rawZone.includes("중립")) return "neutral";
  return "none";
}

function detectRiskLevel(result) {
  const rawRisk = `${result?.riskLevel || result?.analysis?.riskLevel || result?.analysis?.summary?.riskLevel || ""}`.toLowerCase();
  if (rawRisk.includes("high") || rawRisk.includes("높")) return "high";
  if (rawRisk.includes("low") || rawRisk.includes("낮")) return "low";
  return "medium";
}

function firstSentenceOrPreview(value) {
  if (typeof value !== "string") return "";
  const text = value.trim();
  if (!text) return "";

  const firstLine = text.split("\n").find((line) => line.trim()) || text;
  const sentenceMatch = firstLine.match(/^.+?[.!?。！？](\s|$)/);
  const preview = (sentenceMatch?.[0] || firstLine).trim();

  return preview.length > 120 ? `${preview.slice(0, 120).trim()}...` : preview;
}

function buildDecisionCardData(result, searchParams) {
  const userMode = detectUserMode(result, searchParams);
  const fallback = userMode === "holder" ? holderFallback : viewerFallback;
  const decision = result?.decision || result?.lunaDecision || result?.analysis?.decision || {};
  const aiOpinion = result?.aiOpinion || {};
  const aiSummary = typeof aiOpinion?.summary === "string" ? aiOpinion.summary.trim() : "";
  const aiReasonSummary = firstSentenceOrPreview(aiOpinion?.commentary);

  const actions = [
    ...toArray(decision.actions),
    ...toArray(decision.actionList),
    ...toArray(result?.actions)
  ];

  const recheckConditions = [
    ...toArray(decision.recheckConditions),
    ...toArray(decision.recheckConditionList),
    ...toArray(decision.recheck),
    ...toArray(result?.recheckConditions)
  ];

  return {
    userMode,
    zone: detectZone(result),
    headline: decision.headline || decision.conclusion || aiSummary || fallback.headline,
    reasonSummary: decision.reasonSummary || decision.reason || aiReasonSummary || fallback.reasonSummary,
    actions: actions.length > 0 ? actions : fallback.actions,
    recheckConditions: recheckConditions.length > 0 ? recheckConditions : fallback.recheckConditions,
    riskLevel: detectRiskLevel(result)
  };
}

export default function ResultClient() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [sheetOpen, setSheetOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function requestOnce() {
      const res = await fetch(`/api/proxy-analyze?${searchParams.toString()}`, {
        cache: "no-store"
      });

      const contentType = res.headers.get("content-type") || "";
      if (!contentType.includes("application/json")) {
        const text = await res.text();
        throw new Error(text?.slice(0, 120) || "분석 서버가 잠깐 불안정해.");
      }

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "분석 요청에 실패했어");
      }

      return data;
    }

    async function run() {
      setLoading(true);
      setError("");

      try {
        let data;
        try {
          data = await requestOnce();
        } catch (firstErr) {
          data = await requestOnce();
        }

        if (!cancelled) {
          setResult(data);
        }
      } catch (e) {
        if (!cancelled) {
          setError(e.message || "오류가 발생했어");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    run();

    return () => {
      cancelled = true;
    };
  }, [searchParams]);

  if (loading) return <LoadingView />;

  if (error) {
    return (
      <main style={pageStyle}>
        <div style={wrapperStyle}>
          <div
            style={{
              ...cardStyle,
              border: "1px solid #FF5C5C",
              background: "#2A1217",
              color: "#ffffff",
              marginBottom: 20
            }}
          >
            {error}
          </div>
          <button
            onClick={() => router.push("/")}
            style={{
              borderRadius: 14,
              border: "none",
              background: "#4DA3FF",
              color: "#0B0F14",
              padding: "12px 18px",
              fontWeight: 700
            }}
          >
            입력 화면으로 돌아가기
          </button>
        </div>
      </main>
    );
  }

  const analysis = result?.analysis || {};
  const personalization = result?.personalization || {};
  const summary = analysis?.summary || {};
  const country = result?.instrument?.country;
  const currentPrice = formatPriceOrDash(summary?.currentPrice, country);
  const support = formatPriceOrDash(summary?.activeSupport ?? summary?.support, country);
  const resistance = formatPriceOrDash(summary?.activeResistance ?? summary?.resistance, country);
  const volumeRatio = summary?.volumeRatio ? `${formatNumberOrDash(summary?.volumeRatio, country)}배` : "-";
  const aiOpinion = result?.aiOpinion || {};
  const aiSummary = formatPriceText(aiOpinion?.summary || "지금은 루나 한 줄 요약을 잠깐 못 불러왔어.", country);
  const aiCommentary = formatPriceText(aiOpinion?.commentary || "오빠, 지금은 해설을 잠깐 못 불러왔어. 다시 눌러보자.", country);
  const decisionCardData = buildDecisionCardData(result, searchParams);

  return (
    <main style={pageStyle}>
      <div style={{ ...wrapperStyle, maxWidth: 960 }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            gap: 12,
            alignItems: "center",
            marginBottom: 14
          }}
        >
          <button
            onClick={() => router.push("/")}
            style={{
              borderRadius: 14,
              border: "1px solid #263241",
              background: "#121821",
              color: "#F3F6FA",
              padding: "10px 14px",
              fontWeight: 700
            }}
          >
            ← 다시 입력
          </button>

          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", justifyContent: "flex-end" }}>
            <span style={chipStyle}>{result?.ticker || "-"}</span>
            <span style={chipStyle}>{personalization?.holderView || "-"}</span>
            <span style={chipStyle}>{personalization?.styleLabel || "-"}</span>
          </div>
        </div>

        <DecisionCard {...decisionCardData} />

        <div style={{ ...cardStyle, padding: 16 }}>
          <div style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 28, fontWeight: 800 }}>{currentPrice}</div>
            <div style={{ color: "#A7B0BD", marginTop: 6 }}>
              {result?.stateHint || summary?.state || "상태 확인중"}
            </div>
          </div>

          <CandleChart
            chartData={analysis.chart}
            support={summary?.activeSupport ?? summary?.support}
            resistance={summary?.activeResistance ?? summary?.resistance}
            country={country}
          />

          <div
            style={{
              marginTop: 14,
              display: "grid",
              gridTemplateColumns: "1fr",
              gap: 12
            }}
          >
            <div style={summaryCardStyle}>
              <div style={{ color: "#A7B0BD", fontSize: 13, marginBottom: 8, fontWeight: 700 }}>기술 요약</div>
              <SummaryRow label="현재가" value={currentPrice} />
              <SummaryRow label="이평선" value={movingAverageText(summary, country)} />
              <SummaryRow label="지지" value={support} />
              <SummaryRow label="저항" value={resistance} />
              <SummaryRow label="거래량" value={volumeRatio} />
            </div>
          </div>
        </div>
      </div>

      <button
        onClick={() => setSheetOpen(true)}
        style={{
          position: "fixed",
          left: 16,
          right: 16,
          bottom: 16,
          borderRadius: 18,
          border: "none",
          background: "#4DA3FF",
          color: "#0B0F14",
          padding: "16px 18px",
          fontSize: 17,
          fontWeight: 800,
          boxShadow: "0 12px 24px rgba(77,163,255,0.35)",
          zIndex: 30
        }}
      >
        루나 해설 보기
      </button>

      <BottomSheet open={sheetOpen} onClose={() => setSheetOpen(false)}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <div style={{ fontSize: 20, fontWeight: 800, color: "#F3F6FA" }}>루나 해설</div>
          <button
            onClick={() => setSheetOpen(false)}
            style={{
              border: "1px solid #263241",
              background: "#171F2A",
              color: "#F3F6FA",
              borderRadius: 12,
              padding: "8px 12px",
              fontWeight: 700
            }}
          >
            닫기
          </button>
        </div>

        <div
          style={{
            whiteSpace: "pre-wrap",
            lineHeight: 1.9,
            color: "#F3F6FA",
            fontSize: 16
          }}
        >
          <div style={{ fontWeight: 700, marginBottom: 10 }}>{aiSummary}</div>
          <div>{aiCommentary}</div>
        </div>
      </BottomSheet>
    </main>
  );
}
