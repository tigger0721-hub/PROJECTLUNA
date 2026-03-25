const PRICE_CONTEXT_PATTERN = /(현재가|가격|지지|저항|목표|매물|종가|고가|저가|라인|밴드|price|support|resistance)/i;

export function formatNumber(value, country) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "-";

  if (country === "US") {
    return number.toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }

  return Math.round(number).toLocaleString("ko-KR", {
    maximumFractionDigits: 0
  });
}

export function formatPrice(value, country) {
  const numberText = formatNumber(value, country);
  if (numberText === "-") return "-";

  if (country === "US") {
    return `$${numberText}`;
  }

  return `${numberText}원`;
}

function looksLikePrice(text, index, rawNumber) {
  const before = text.slice(Math.max(0, index - 8), index);
  const after = text.slice(index + rawNumber.length, index + rawNumber.length + 8);
  const nextNonSpace = after.trimStart()[0] || "";
  const prevNonSpace = before.trimEnd().slice(-1);

  if (nextNonSpace === "%" || nextNonSpace === "일") return false;
  if (nextNonSpace === "원" || nextNonSpace === "$" || prevNonSpace === "$") return true;
  if (PRICE_CONTEXT_PATTERN.test(before) || PRICE_CONTEXT_PATTERN.test(after)) return true;

  return Number(rawNumber.replace(/,/g, "")) >= 1000;
}

export function formatPriceText(text, country) {
  if (!text) return text;

  return text.replace(/\d[\d,]*(?:\.\d+)?/g, (rawNumber, index) => {
    if (!looksLikePrice(text, index, rawNumber)) return rawNumber;

    const normalized = Number(rawNumber.replace(/,/g, ""));
    const nextChar = text.slice(index + rawNumber.length).trimStart()[0] || "";
    const prevChar = text.slice(0, index).trimEnd().slice(-1);

    if (country === "US") {
      if (prevChar === "$") return formatNumber(normalized, country);
      return formatPrice(normalized, country);
    }

    if (nextChar === "원") return formatNumber(normalized, country);
    return formatPrice(normalized, country);
  });
}
