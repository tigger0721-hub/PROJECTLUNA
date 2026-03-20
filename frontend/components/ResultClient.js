"use client";
import { useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import CandleChart from "@/components/CandleChart";

const pageStyle = {
  minHeight: "100vh",
  background: "linear-gradient(to bottom, #020617, #0f172a)",
  padding: "24px 16px"
};

const wrapperStyle = {
  maxWidth: 1100,
  margin: "0 auto"
};

const cardStyle = {
  background: "rgba(15,23,42,0.88)",
  border: "1px solid #334155",
  borderRadius: 24,
  padding: 24,
  boxShadow: "0 10px 30px rgba(0,0,0,0.25)"
};

const sectionTitle = {
  fontSize: 22,
  fontWeight: 800,
  marginBottom: 16
};

const statGridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
  gap: 12
};

const statBoxStyle = {
  background: "#1e293b",
  borderRadius: 18,
  padding: 16
};

function StatBox({ label, value }) {
  return (
    <div style={statBoxStyle}>
      <div style={{ fontSize: 13, color: "#94a3b8" }}>{label}</div>
      <div style={{ fontSize: 19, fontWeight: 700, marginTop: 6 }}>{value}</div>
    </div>
  );
}

function LoadingView() {
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
          <div style={{ marginBottom: 20 }}>
            <img
              src="/luna-loading.png"
              alt="루나 로딩 이미지"
              style={{
                width: "min(260px, 70vw)",
                height: "auto",
                borderRadius: 20
              }}
            />
          </div>

          <h1 style={{ margin: 0, fontSize: 28, lineHeight: 1.25 }}>
            루나가 차트 분석중{dots}
          </h1>

          <p
            style={{
              marginTop: 14,
              color: "#cbd5e1",
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

          <div style={{ marginTop: 16, color: "#94a3b8", fontSize: 14 }}>
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
          0% {
            transform: translateX(-120%);
          }
          100% {
            transform: translateX(320%);
          }
        }
      `}</style>
    </main>
  );
}

export default function ResultPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  useEffect(() => {
    async function run() {
      setLoading(true);
      setError("");

      try {
        const res = await fetch(`/api/proxy-analyze?${searchParams.toString()}`, {
          cache: "no-store"
        });

        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || "분석 요청에 실패했어");
        }

        setResult(data);
      } catch (e) {
        setError(e.message || "오류가 발생했어");
      } finally {
        setLoading(false);
      }
    }

    run();
  }, [searchParams]);

  if (loading) {
    return <LoadingView />;
  }

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

  const analysis = result.analysis;
  const personalization = result.personalization;

  return (
    <main style={pageStyle}>
      <div style={wrapperStyle}>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center", marginBottom: 20 }}>
          <button
            onClick={() => router.push("/")}
            style={{
              borderRadius: 14,
              border: "1px solid #475569",
              background: "#0f172a",
              color: "#fff",
              padding: "12px 18px",
              fontWeight: 700
            }}
          >
            ← 입력 다시 하기
          </button>
          <div style={{ color: "#cbd5e1" }}>{result.ticker} 분석 결과</div>
        </div>

        <div style={{ display: "grid", gap: 24 }}>
          <div style={cardStyle}>
            <div style={sectionTitle}>캔들차트</div>
            <CandleChart
              chartData={analysis.chart}
              support={analysis.summary.support}
              resistance={analysis.summary.resistance}
            />
            <div style={{ color: "#94a3b8", fontSize: 13, marginTop: 10 }}>
              최근 약 3개월 구간 위주로 표시해서 가시성을 높였어.
            </div>
          </div>

          <div style={cardStyle}>
            <div style={sectionTitle}>핵심 요약</div>
            <div style={statGridStyle}>
              <StatBox label="종목" value={result.ticker} />
              <StatBox label="현재 상태" value={analysis.summary.state} />
              <StatBox label="현재가" value={analysis.summary.currentPrice} />
              <StatBox label="지지선 후보" value={analysis.summary.support} />
              <StatBox label="저항선 후보" value={analysis.summary.resistance} />
              <StatBox label="거래량 배수" value={`${analysis.summary.volumeRatio}배`} />
            </div>
          </div>

          <div style={cardStyle}>
            <div style={sectionTitle}>개인화 요약</div>
            <div style={statGridStyle}>
              <StatBox label="모드" value={personalization.holderView} />
              <StatBox label="투자 성향" value={personalization.styleLabel} />
              <StatBox label="권장 추가매수 구간" value={personalization.suggestedAddBuyZone} />
              <StatBox label="권장 손절 기준" value={personalization.suggestedStop} />
              <StatBox label="1차 익절 후보" value={personalization.suggestedTakeProfit} />
              <StatBox
                label="현재 손익률"
                value={personalization.pnlPercent == null ? "-" : `${personalization.pnlPercent}%`}
              />
            </div>
          </div>

          <div style={cardStyle}>
            <div style={sectionTitle}>기술적 해설</div>
            <div style={{ lineHeight: 1.85, color: "#e2e8f0" }}>{analysis.explanation || analysis.trendSummary || "루나가 흐름을 다시 정리중이야."}</div>
            <ul style={{ marginTop: 16, color: "#cbd5e1", lineHeight: 1.8 }}>
              {(analysis.lessons || []).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>

          <div style={cardStyle}>
            <div style={sectionTitle}>루나의 종합 의견</div>
            <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.95, color: "#e2e8f0" }}>
              {result.aiOpinion}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}