"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import CandleChart from "@/components/CandleChart";

const pageStyle = {
  minHeight: "100vh",
  background: "#f8fafc",
  color: "#0f172a",
  padding: "16px 12px 96px"
};

const wrapperStyle = {
  maxWidth: 1100,
  margin: "0 auto"
};

const cardStyle = {
  background: "#ffffff",
  border: "1px solid #e2e8f0",
  borderRadius: 24,
  padding: 18,
  boxShadow: "0 10px 24px rgba(15,23,42,0.08)"
};

const chipStyle = {
  display: "inline-flex",
  alignItems: "center",
  gap: 6,
  borderRadius: 999,
  background: "#eff6ff",
  color: "#1e293b",
  fontSize: 13,
  padding: "8px 12px"
};

const summaryCardStyle = {
  background: "#0f172a",
  borderRadius: 18,
  padding: 14
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
              color: "#475569",
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
              background: "#1e293b",
              borderRadius: 9999,
              overflow: "hidden",
              position: "relative"
            }}
          >
            <div className="loading-bar" />
          </div>

          <div style={{ marginTop: 16, color: "#64748b", fontSize: 14 }}>
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
          background: linear-gradient(90deg, #60a5fa, #3b82f6);
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
          background: "#ffffff",
          borderTopLeftRadius: 24,
          borderTopRightRadius: 24,
          border: "1px solid #e2e8f0",
          boxShadow: "0 -10px 30px rgba(15,23,42,0.12)",
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
            background: "#334155",
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
        borderBottom: "1px solid rgba(71,85,105,0.4)"
      }}
    >
      <div style={{ color: "#94a3b8", fontSize: 14 }}>{label}</div>
      <div style={{ color: "#f8fafc", fontWeight: 700, textAlign: "right" }}>{value}</div>
    </div>
  );
}

function numberOrDash(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  return Number(value).toLocaleString("ko-KR", { maximumFractionDigits: 2 });
}

function movingAverageText(summary) {
  const ma5 = numberOrDash(summary?.ma5);
  const ma20 = numberOrDash(summary?.ma20);
  const ma60 = numberOrDash(summary?.ma60);
  const ma120 = numberOrDash(summary?.ma120);
  return `5일 ${ma5} / 20일 ${ma20} / 60일 ${ma60} / 120일 ${ma120}`;
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
          <div style={{ ...cardStyle, border: "1px solid #7f1d1d", background: "#450a0a", marginBottom: 20 }}>
            {error}
          </div>
          <button
            onClick={() => router.push("/")}
            style={{
              borderRadius: 14,
              border: "none",
              background: "#2563eb",
              color: "#fff",
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
  const currentPrice = numberOrDash(summary?.currentPrice);
  const support = numberOrDash(summary?.support);
  const resistance = numberOrDash(summary?.resistance);
  const volumeRatio = summary?.volumeRatio ? `${numberOrDash(summary?.volumeRatio)}배` : "-";
  const aiOpinion = result?.aiOpinion || {};
  const aiSummary = aiOpinion?.summary || "지금은 루나 한 줄 요약을 잠깐 못 불러왔어.";
  const aiCommentary = aiOpinion?.commentary || "오빠, 지금은 해설을 잠깐 못 불러왔어. 다시 눌러보자.";

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
              border: "1px solid #334155",
              background: "#ffffff",
              color: "#0f172a",
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

        <div style={{ ...cardStyle, padding: 16 }}>
          <div style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 28, fontWeight: 800 }}>{currentPrice}</div>
            <div style={{ color: "#94a3b8", marginTop: 6 }}>
              {result?.stateHint || summary?.state || "상태 확인중"}
            </div>
          </div>

          <CandleChart
            chartData={analysis.chart}
            support={summary.support}
            resistance={summary.resistance}
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
              <div style={{ color: "#64748b", fontSize: 13, marginBottom: 8 }}>기술 요약</div>
              <SummaryRow label="현재가" value={currentPrice} />
              <SummaryRow label="이평선" value={movingAverageText(summary)} />
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
          background: "#2563eb",
          color: "#fff",
          padding: "16px 18px",
          fontSize: 17,
          fontWeight: 800,
          boxShadow: "0 12px 24px rgba(37,99,235,0.35)",
          zIndex: 30
        }}
      >
        루나 해설 보기
      </button>

      <BottomSheet open={sheetOpen} onClose={() => setSheetOpen(false)}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <div style={{ fontSize: 20, fontWeight: 800 }}>루나 해설</div>
          <button
            onClick={() => setSheetOpen(false)}
            style={{
              border: "1px solid #334155",
              background: "#ffffff",
              color: "#0f172a",
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
            color: "#0f172a",
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
