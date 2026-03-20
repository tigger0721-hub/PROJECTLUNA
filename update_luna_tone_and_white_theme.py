from pathlib import Path

ROOT = Path(__file__).resolve().parent

files = {
    "backend": ROOT / "backend" / "main.py",
    "page": ROOT / "frontend" / "app" / "page.js",
    "result_client": ROOT / "frontend" / "components" / "ResultClient.js",
}

replacements = {
    files["backend"]: [
        (
            '- 말투는 친근하되 냉정하게 하고, 필요하면 아주 약하게 현실적인 표현을 섞어도 된다.\n'
            '- 예: "좀 꼬일 수 있어", "지금 들어가면 살짝 무리일 수 있어", "여기서 급하게 들어가면 조질 수도 있어 보여"\n'
            '- 하지만 이런 표현은 과하지 않게 아주 가끔만 써라.\n',
            '- 말투는 오빠에게 말하듯 자연스러운 반말로 하고, 너무 딱딱한 보고서체는 쓰지 마라.\n'
            '- "~입니다" 대신 "~야", "~해", "~하는 게 맞아", "~가 더 나아 보여" 같은 표현을 기본으로 써라.\n'
            '- 예: "오빠 이건 좀 애매한 자리야", "괜히 여기서 타면 꼬일 수 있어", "지금은 기다리는 게 더 나아 보여"\n'
            '- 필요하면 가볍게 현실적인 표현을 섞어도 되지만 너무 과하게 쓰진 마라.\n'
        ),
        (
            '8. 말투는 친근하고 자연스럽게 하되, 과장하거나 허세 섞인 표현은 피한다.\n'
            '9. 필요할 때만 아주 가볍게 구어체를 섞어도 된다.\n',
            '8. 사용자를 "오빠"라고 부르며 자연스러운 반말로 말한다.\n'
            '9. "~입니다" 같은 딱딱한 문체는 쓰지 말고, "~야", "~해", "~가 더 나아 보여" 같은 말투를 기본으로 한다.\n'
            '10. 과장하거나 허세 섞인 표현은 피하고, 같이 차트 보면서 말해주는 느낌으로 답한다.\n'
        ),
        (
            '        return {\n'
            '            "ticker": ticker.upper(),\n'
            '            "analysis": analysis,\n'
            '            "personalization": personalization,\n'
            '            "stateHint": build_state_hint(\n',
            '        analysis["explanation"] = analysis["trendSummary"]\n'
            '        analysis["lessons"] = []\n'
            '\n'
            '        return {\n'
            '            "ticker": ticker.upper(),\n'
            '            "analysis": analysis,\n'
            '            "personalization": personalization,\n'
            '            "stateHint": build_state_hint(\n'
        ),
    ],
    files["page"]: [
        (
            'const pageStyle = {\n'
            '  minHeight: "100vh",\n'
            '  background: "linear-gradient(to bottom, #020617, #0f172a)",\n'
            '  padding: "24px 16px"\n'
            '};\n',
            'const pageStyle = {\n'
            '  minHeight: "100vh",\n'
            '  background: "#f8fafc",\n'
            '  color: "#0f172a",\n'
            '  padding: "24px 16px"\n'
            '};\n'
        ),
        (
            'const cardStyle = {\n'
            '  background: "rgba(15,23,42,0.88)",\n'
            '  border: "1px solid #334155",\n'
            '  borderRadius: 24,\n'
            '  padding: 24,\n'
            '  boxShadow: "0 10px 30px rgba(0,0,0,0.25)"\n'
            '};\n',
            'const cardStyle = {\n'
            '  background: "#ffffff",\n'
            '  border: "1px solid #e2e8f0",\n'
            '  borderRadius: 24,\n'
            '  padding: 24,\n'
            '  boxShadow: "0 10px 24px rgba(15,23,42,0.08)"\n'
            '};\n'
        ),
        (
            '  background: "#020617",\n'
            '  color: "#f8fafc",\n',
            '  background: "#ffffff",\n'
            '  color: "#0f172a",\n'
        ),
        (
            '  border: "1px solid #475569",\n',
            '  border: "1px solid #cbd5e1",\n'
        ),
        (
            '  marginBottom: 8,\n'
            '  color: "#cbd5e1",\n',
            '  marginBottom: 8,\n'
            '  color: "#475569",\n'
        ),
        (
            '          <p style={{ color: "#cbd5e1", fontSize: 18, marginTop: 12, lineHeight: 1.7 }}>\n',
            '          <p style={{ color: "#475569", fontSize: 18, marginTop: 12, lineHeight: 1.7 }}>\n'
        ),
        (
            '            <div style={{ color: "#94a3b8", fontSize: 13 }}>\n',
            '            <div style={{ color: "#64748b", fontSize: 13 }}>\n'
        ),
    ],
    files["result_client"]: [
        (
            'const pageStyle = {\n'
            '  minHeight: "100vh",\n'
            '  background: "linear-gradient(to bottom, #020617, #0f172a)",\n'
            '  padding: "16px 12px 96px"\n'
            '};\n',
            'const pageStyle = {\n'
            '  minHeight: "100vh",\n'
            '  background: "#f8fafc",\n'
            '  color: "#0f172a",\n'
            '  padding: "16px 12px 96px"\n'
            '};\n'
        ),
        (
            'const cardStyle = {\n'
            '  background: "rgba(15,23,42,0.88)",\n'
            '  border: "1px solid #334155",\n'
            '  borderRadius: 24,\n'
            '  padding: 18,\n'
            '  boxShadow: "0 10px 30px rgba(0,0,0,0.25)"\n'
            '};\n',
            'const cardStyle = {\n'
            '  background: "#ffffff",\n'
            '  border: "1px solid #e2e8f0",\n'
            '  borderRadius: 24,\n'
            '  padding: 18,\n'
            '  boxShadow: "0 10px 24px rgba(15,23,42,0.08)"\n'
            '};\n'
        ),
        (
            'const chipStyle = {\n'
            '  display: "inline-flex",\n'
            '  alignItems: "center",\n'
            '  gap: 6,\n'
            '  borderRadius: 999,\n'
            '  background: "#1e293b",\n'
            '  color: "#e2e8f0",\n'
            '  fontSize: 13,\n'
            '  padding: "8px 12px"\n'
            '};\n',
            'const chipStyle = {\n'
            '  display: "inline-flex",\n'
            '  alignItems: "center",\n'
            '  gap: 6,\n'
            '  borderRadius: 999,\n'
            '  background: "#eff6ff",\n'
            '  color: "#1e293b",\n'
            '  fontSize: 13,\n'
            '  padding: "8px 12px"\n'
            '};\n'
        ),
        (
            '              color: "#cbd5e1",\n',
            '              color: "#475569",\n'
        ),
        (
            '          <div style={{ marginTop: 16, color: "#94a3b8", fontSize: 14 }}>\n',
            '          <div style={{ marginTop: 16, color: "#64748b", fontSize: 14 }}>\n'
        ),
        (
            '              border: "1px solid #475569",\n'
            '              background: "#0f172a",\n'
            '              color: "#fff",\n',
            '              border: "1px solid #cbd5e1",\n'
            '              background: "#ffffff",\n'
            '              color: "#0f172a",\n'
        ),
        (
            '          <div style={{ color: "#cbd5e1" }}>{result.ticker} 분석 결과</div>\n',
            '          <div style={{ color: "#334155" }}>{result.ticker} 분석 결과</div>\n'
        ),
        (
            '              <div style={{ color: "#94a3b8", fontSize: 13, marginBottom: 8 }}>기술 요약</div>\n',
            '              <div style={{ color: "#64748b", fontSize: 13, marginBottom: 8 }}>기술 요약</div>\n'
        ),
        (
            '          background: "#0f172a",\n'
            '          borderTopLeftRadius: 24,\n'
            '          borderTopRightRadius: 24,\n'
            '          border: "1px solid #334155",\n'
            '          boxShadow: "0 -10px 30px rgba(0,0,0,0.35)",\n',
            '          background: "#ffffff",\n'
            '          borderTopLeftRadius: 24,\n'
            '          borderTopRightRadius: 24,\n'
            '          border: "1px solid #e2e8f0",\n'
            '          boxShadow: "0 -10px 30px rgba(15,23,42,0.12)",\n'
        ),
        (
            '            width: 56,\n'
            '            height: 6,\n'
            '            borderRadius: 999,\n'
            '            background: "#475569",\n',
            '            width: 56,\n'
            '            height: 6,\n'
            '            borderRadius: 999,\n'
            '            background: "#cbd5e1",\n'
        ),
        (
            '              border: "1px solid #475569",\n'
            '              background: "#0f172a",\n'
            '              color: "#fff",\n',
            '              border: "1px solid #cbd5e1",\n'
            '              background: "#ffffff",\n'
            '              color: "#0f172a",\n'
        ),
        (
            '            color: "#e2e8f0",\n',
            '            color: "#0f172a",\n'
        ),
    ],
}

for path, items in replacements.items():
    if not path.exists():
        print(f"[SKIP] 파일 없음: {path}")
        continue

    text = path.read_text(encoding="utf-8")
    original = text

    for old, new in items:
        if old in text:
            text = text.replace(old, new)
        else:
            print(f"[WARN] 패턴 못 찾음: {path.name}\n---\n{old[:120]}...\n")

    if text != original:
        path.write_text(text, encoding="utf-8")
        print(f"[OK] 수정 완료: {path}")
    else:
        print(f"[NOCHANGE] 변경 없음: {path}")

print("\n끝! 이제 git add / commit / push 하면 돼.")