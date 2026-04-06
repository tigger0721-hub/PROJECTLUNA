import { NextResponse } from "next/server";

export async function GET(request) {
  const { searchParams } = new URL(request.url);
  const ticker = searchParams.get("ticker") || "";
  const mode = searchParams.get("mode") || "viewer";
  const avgPrice = searchParams.get("avg_price") || "";
  const quantity = searchParams.get("quantity") || "";
  const style = searchParams.get("style") || "conservative";
  const marketHint = searchParams.get("market_hint") || "auto";
  const normalizedMarketHint = ["auto", "KR", "US"].includes(marketHint)
    ? marketHint
    : "auto";

  const backendBase = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

  const qs = new URLSearchParams();
  qs.set("ticker", ticker);
  qs.set("mode", mode);
  qs.set("style", style);
  qs.set("market_hint", normalizedMarketHint);

  if (mode === "holder") {
    if (avgPrice !== "") qs.set("avg_price", avgPrice);
    if (quantity !== "") qs.set("quantity", quantity);
  }

  try {
    const response = await fetch(`${backendBase}/api/analyze?${qs.toString()}`, {
      cache: "no-store"
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json(
      { detail: `백엔드 연결 실패: ${String(error)}` },
      { status: 500 }
    );
  }
}
