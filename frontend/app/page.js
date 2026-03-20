"use client";

import { useState } from "react";

const pageStyle = {
  minHeight: "100vh",
  background: "linear-gradient(to bottom, #020617, #0f172a)",
  padding: "24px 16px"
};

const wrapperStyle = {
  maxWidth: 720,
  margin: "0 auto"
};

const cardStyle = {
  background: "rgba(15,23,42,0.88)",
  border: "1px solid #334155",
  borderRadius: 24,
  padding: 24,
  boxShadow: "0 10px 30px rgba(0,0,0,0.25)"
};

const inputStyle = {
  width: "100%",
  minWidth: 0,
  maxWidth: "100%",
  borderRadius: 16,
  border: "1px solid #475569",
  background: "#020617",
  color: "#f8fafc",
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
  color: "#cbd5e1",
  fontSize: 14,
  display: "block"
};

export default function HomePage() {
  const [mode, setMode] = useState("viewer");

  return (
    <main style={pageStyle}>
      <div style={wrapperStyle}>
        <div style={{ marginBottom: 24 }}>
          <h1 style={{ fontSize: 42, lineHeight: 1.15, margin: 0 }}>루나 차트 해설 MVP</h1>
          <p style={{ color: "#cbd5e1", fontSize: 18, marginTop: 12, lineHeight: 1.7 }}>
            티커와 보유 여부를 기준으로 루나가 차트와 함께 개인화된 분석을 보여줘.
          </p>
        </div>

        <form action="/result" method="get" style={cardStyle}>
          <div style={{ display: "grid", gap: 16 }}>
            <div>
              <label style={labelStyle}>티커</label>
              <input
                name="ticker"
                defaultValue="AAPL.US"
                placeholder="예: AAPL.US"
                style={inputStyle}
                required
              />
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
                <option value="trend">추세형</option>
                <option value="pullback">눌림매수형</option>
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

            <div style={{ color: "#94a3b8", fontSize: 13 }}>
              예시: AAPL.US / TSLA.US / NVDA.US
            </div>
          </div>
        </form>
      </div>
    </main>
  );
}
