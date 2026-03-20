import { Suspense } from "react";
import ResultClient from "@/components/ResultClient";

export const dynamic = "force-dynamic";

export default function ResultPage() {
  return (
    <Suspense fallback={<div style={{ padding: 24, color: "#fff" }}>로딩중...</div>}>
      <ResultClient />
    </Suspense>
  );
}
