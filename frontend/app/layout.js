export const metadata = {
  title: "Luna Chart Tutor",
  description: "루나 차트 해설형 주식 분석 MVP"
};

export default function RootLayout({ children }) {
  return (
    <html lang="ko">
      <body style={{ margin: 0, background: "#020617", color: "#f8fafc", fontFamily: "Arial, sans-serif" }}>
        {children}
      </body>
    </html>
  );
}
