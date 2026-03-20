#!/usr/bin/env bash
set -e

PROJECT_NAME="stock-chart-tutor"

echo "[1/8] Creating folders..."
mkdir -p "$PROJECT_NAME/backend"
mkdir -p "$PROJECT_NAME/frontend/app"
mkdir -p "$PROJECT_NAME/frontend/public"

cd "$PROJECT_NAME"

echo "[2/8] Writing backend files..."
cat > backend/requirements.txt << 'REQEOF'
fastapi==0.115.0
uvicorn[standard]==0.30.6
REQEOF

cat > backend/main.py << 'PYEOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Stock Chart Tutor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"ok": True}

@app.get("/api/hello")
async def hello():
    return {
        "message": "FastAPI backend is running",
        "app": "stock-chart-tutor"
    }
PYEOF

echo "[3/8] Writing frontend files..."
cat > frontend/package.json << 'JSEOF'
{
  "name": "stock-chart-tutor-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev -H 0.0.0.0 -p 3000",
    "build": "next build",
    "start": "next start -H 0.0.0.0 -p 3000"
  },
  "dependencies": {
    "next": "14.2.14",
    "react": "18.3.1",
    "react-dom": "18.3.1"
  }
}
JSEOF

cat > frontend/next.config.js << 'JSEOF'
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
};

module.exports = nextConfig;
JSEOF

cat > frontend/jsconfig.json << 'JSEOF'
{
  "compilerOptions": {
    "baseUrl": "."
  }
}
JSEOF

cat > frontend/app/layout.js << 'JSEOF'
export const metadata = {
  title: "Stock Chart Tutor",
  description: "Minimal FastAPI + Next.js starter"
};

export default function RootLayout({ children }) {
  return (
    <html lang="ko">
      <body style={{ margin: 0, fontFamily: "Arial, sans-serif", background: "#0f172a", color: "#f8fafc" }}>
        {children}
      </body>
    </html>
  );
}
JSEOF

cat > frontend/app/page.js << 'JSEOF'
async function getBackendData() {
  try {
    const baseUrl = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";
    const res = await fetch(`${baseUrl}/api/hello`, { cache: "no-store" });
    if (!res.ok) {
      throw new Error("Backend request failed");
    }
    return await res.json();
  } catch (error) {
    return {
      message: "Backend not reachable yet",
      error: String(error)
    };
  }
}

export default async function HomePage() {
  const data = await getBackendData();

  return (
    <main style={{ maxWidth: 900, margin: "0 auto", padding: 40 }}>
      <h1 style={{ fontSize: 36, marginBottom: 12 }}>차트 해설 MVP</h1>
      <p style={{ fontSize: 18, color: "#cbd5e1", marginBottom: 24 }}>
        FastAPI + Next.js 최소 실행 버전
      </p>

      <div style={{
        background: "#1e293b",
        borderRadius: 16,
        padding: 24,
        marginBottom: 20
      }}>
        <h2 style={{ marginTop: 0 }}>프론트엔드 상태</h2>
        <p>Next.js 앱이 정상 실행 중이야.</p>
      </div>

      <div style={{
        background: "#1e293b",
        borderRadius: 16,
        padding: 24
      }}>
        <h2 style={{ marginTop: 0 }}>백엔드 응답</h2>
        <pre style={{
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
          background: "#0f172a",
          padding: 16,
          borderRadius: 12,
          overflowX: "auto"
        }}>
{JSON.stringify(data, null, 2)}
        </pre>
      </div>
    </main>
  );
}
JSEOF

cat > frontend/.env.local << 'ENVEOF'
NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000
ENVEOF

echo "[4/8] Checking Python..."
python3 --version

echo "[5/8] Creating backend virtualenv..."
python3 -m venv backend/.venv

echo "[6/8] Installing backend packages..."
backend/.venv/bin/pip install --upgrade pip
backend/.venv/bin/pip install -r backend/requirements.txt

echo "[7/8] Checking Node..."
node -v
npm -v

echo "[8/8] Installing frontend packages..."
cd frontend
npm install
cd ..

echo
echo "Setup complete."
echo
echo "Run backend:"
echo "cd $PROJECT_NAME/backend && source .venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000"
echo
echo "Run frontend:"
echo "cd $PROJECT_NAME/frontend && npm run dev"
echo
echo "Open in browser:"
echo "http://YOUR_SERVER_IP:3000"
