"use client";

import { useState } from "react";

const pageStyle = {
  minHeight: "100vh",
  background: "#f8fafc",
  color: "#0f172a",
  padding: "24px 16px"
};

const wrapperStyle = {
  maxWidth: 720,
  margin: "0 auto"
};

const cardStyle = {
  background: "#ffffff",
  border: "1px solid #e2e8f0",
  borderRadius: 24,
  padding: 24,
  boxShadow: "0 10px 24px rgba(15,23,42,0.08)"
};

const inputStyle = {
  width: "100%",
  minWidth: 0,
  maxWidth: "100%",
  borderRadius: 16,
  border: "1px solid #cbd5e1",
  background: "#ffffff",
  color: "#0f172a",
  padding: "14px 16px",
  fontSize: 17,
  outline: "none",
  boxSizing: "border-box"
};

const buttonStyle = {
  borderRadius: 16,
  border: "none",
  background: "#2563eb",
  color: "#fff",
  padding: "14px 22px",
  fontSize: 18,
  fontWeight: 700,
  cursor: "pointer"
};

const labelStyle = {
  marginBottom: 8,
  color: "#475569",
  fontSize: 14,
  display: "block"
};

export default function HomePage() {
  const [mode, setMode] = useState("viewer");
  const [marketHint, setMarketHint] = useState("auto");

  const marketOptions = [
    { value: "auto", label: "자동" },
    { value: "KR", label: "국내" },
    { value: "US", label: "미국" }
  ];

  return (
    <main style={pageStyle}>
      <div style={wrapperStyle}>
        <div style={{ marginBottom: 24 }}>
          <h1 style={{ fontSize: 42, lineHeight: 1.15, margin: 0 }}>루나 차트 해설 MVP</h1>
          <p style={{ color: "#475569", fontSize: 18, marginTop: 12, lineHeight: 1.7 }}>
            미국/국내 종목명 또는 티커·코드를 입력하면 루나가 차트와 함께 개인화된 분석을 보여줘.
          </p>
        </div>

        <form action="/result" method="get" style={cardStyle}>
          <div style={{ display: "grid", gap: 16 }}>
            <div>
              <label style={labelStyle}>종목 검색</label>
              <input
                name="ticker"
                defaultValue="NVDA"
                placeholder="종목명 또는 티커 입력 (예: 엔비디아, NVDA, 삼성전자, 005930)"
                style={inputStyle}
                required
              />
              <input type="hidden" name="market_hint" value={marketHint} />
              <div
                role="tablist"
                aria-label="시장 선택"
                style={{
                  marginTop: 10,
                  display: "inline-flex",
                  gap: 6,
                  padding: 4,
                  borderRadius: 999,
                  border: "1px solid #cbd5e1",
                  background: "#f8fafc"
                }}
              >
                {marketOptions.map((option) => {
                  const active = marketHint === option.value;
                  return (
                    <button
                      key={option.value}
                      type="button"
                      role="tab"
                      aria-selected={active}
                      onClick={() => setMarketHint(option.value)}
                      style={{
                        border: "none",
                        borderRadius: 999,
                        padding: "7px 12px",
                        fontSize: 13,
                        fontWeight: 700,
                        cursor: "pointer",
                        color: active ? "#ffffff" : "#334155",
                        background: active ? "#2563eb" : "transparent"
                      }}
                    >
                      {option.label}
                    </button>
                  );
                })}
              </div>
            </div>

            <div>
              <label style={labelStyle}>보유 여부</label>
              <select
                name="mode"
                value={mode}
                onChange={(e) => setMode(e.target.value)}
                style={inputStyle}
              >
                <option value="viewer">미보유자</option>
                <option value="holder">보유자</option>
              </select>
            </div>

            <div>
              <label style={labelStyle}>투자 성향</label>
              <select name="style" defaultValue="conservative" style={inputStyle}>
                <option value="conservative">보수형</option>
                <option value="pullback">눌림매수형</option>
                <option value="trend">추세매수형</option>
                <option value="swing">단기 스윙형</option>
                <option value="protect_profit">수익보호형</option>
                <option value="trend_partial">추세추종+분할익절형</option>
              </select>
            </div>

            {mode === "holder" ? (
              <>
                <div>
                  <label style={labelStyle}>평단가</label>
                  <input
                    name="avg_price"
                    placeholder="예: 180"
                    style={inputStyle}
                    required={mode === "holder"}
                  />
                </div>
                <div>
                  <label style={labelStyle}>보유수량</label>
                  <input
                    name="quantity"
                    placeholder="예: 10"
                    style={inputStyle}
                    required={mode === "holder"}
                  />
                </div>
              </>
            ) : null}

            <div style={{ marginTop: 4 }}>
              <button type="submit" style={buttonStyle}>
                루나에게 분석 받기
              </button>
            </div>

            <div style={{ color: "#64748b", fontSize: 13 }}>
              예시: 엔비디아 / Nvidia / TSLA / 삼성전자 / 005930 / 알테오젠
            </div>
          </div>
        </form>
      </div>
    </main>
  );
}
