const colors = {
  background: "#0B0F14",
  surface: "#121821",
  card: "#171F2A",
  primaryText: "#F3F6FA",
  secondaryText: "#A7B0BD",
  blue: "#4DA3FF",
  green: "#3DDC97",
  gold: "#F5B84B",
  red: "#FF5C5C",
  border: "#263241"
};

const cardStyle = {
  background: colors.card,
  border: `1px solid ${colors.border}`,
  borderRadius: 24,
  padding: "20px 18px",
  boxShadow: "0 18px 36px rgba(0,0,0,0.24)",
  color: colors.primaryText,
  marginBottom: 16
};

const sectionTitleStyle = {
  margin: "0 0 8px",
  color: colors.secondaryText,
  fontSize: 13,
  fontWeight: 700,
  letterSpacing: "0.02em"
};

const bodyStyle = {
  margin: 0,
  color: colors.primaryText,
  fontSize: 14,
  lineHeight: 1.6
};

function modeLabel(userMode) {
  return userMode === "holder" ? "보유자" : "미보유자";
}

function modeColor(userMode, zone, riskLevel) {
  if (riskLevel === "high") return colors.red;
  if (zone === "profit") return colors.gold;
  if (userMode === "holder") return colors.green;
  return colors.blue;
}

function BulletList({ items }) {
  return (
    <ul
      style={{
        margin: 0,
        padding: 0,
        listStyle: "none",
        display: "grid",
        gap: 8
      }}
    >
      {items.map((item) => (
        <li
          key={item}
          style={{
            display: "flex",
            gap: 8,
            alignItems: "flex-start",
            color: colors.primaryText,
            fontSize: 14,
            lineHeight: 1.55
          }}
        >
          <span
            aria-hidden="true"
            style={{
              width: 6,
              height: 6,
              borderRadius: 999,
              background: colors.blue,
              marginTop: 8,
              flex: "0 0 auto"
            }}
          />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

export default function DecisionCard({
  userMode,
  zone = "none",
  headline,
  reasonSummary,
  actions,
  recheckConditions,
  riskLevel = "medium"
}) {
  const accent = modeColor(userMode, zone, riskLevel);

  return (
    <section style={cardStyle} aria-label="LUNA decision card">
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 12,
          marginBottom: 14
        }}
      >
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
            borderRadius: 999,
            border: `1px solid ${accent}`,
            background: `${accent}1A`,
            color: accent,
            fontSize: 12,
            fontWeight: 800,
            padding: "7px 10px"
          }}
        >
          <span
            style={{
              width: 7,
              height: 7,
              borderRadius: 999,
              background: accent
            }}
          />
          {modeLabel(userMode)}
        </div>
        <div style={{ color: colors.secondaryText, fontSize: 12, fontWeight: 700 }}>
          LUNA 판단
        </div>
      </div>

      <h1
        style={{
          margin: "0 0 16px",
          color: colors.primaryText,
          fontSize: "clamp(22px, 5.8vw, 26px)",
          lineHeight: 1.25,
          fontWeight: 900,
          letterSpacing: "-0.03em"
        }}
      >
        {headline}
      </h1>

      <div
        style={{
          display: "grid",
          gap: 14,
          borderTop: `1px solid ${colors.border}`,
          paddingTop: 16
        }}
      >
        <div>
          <h2 style={sectionTitleStyle}>이유</h2>
          <p style={bodyStyle}>{reasonSummary}</p>
        </div>

        <div>
          <h2 style={sectionTitleStyle}>지금 할 일</h2>
          <BulletList items={actions} />
        </div>

        <div>
          <h2 style={sectionTitleStyle}>다시 볼 조건</h2>
          <BulletList items={recheckConditions} />
        </div>
      </div>
    </section>
  );
}
