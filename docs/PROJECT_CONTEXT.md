# PROJECTLUNA Project Context

## 1. Purpose

PROJECTLUNA is being developed as an AI trading coach service.

The product should not be understood as a simple AI chart explanation app. Its goal is to help users make better trading decisions by guiding them through timing, risk, position management, profit protection, and emotional discipline.

PROJECTLUNA should help users answer practical questions such as:

- Should I enter now or wait?
- If I already hold this stock, should I hold, reduce, or protect profit?
- Am I chasing because of FOMO?
- Is the current price area attractive or risky?
- What condition should I wait for before acting?
- If I am in profit, how do I avoid giving back gains?

The core product direction is:

> PROJECTLUNA is not an AI that explains charts.  
> PROJECTLUNA is an AI trading coach that helps users make better decisions.

## 2. Current Repository State

Repository checked:

- GitHub repository: https://github.com/tigger0721-hub/PROJECTLUNA
- Branch observed: `main`
- Repository visibility: public
- Current top-level structure:
  - `backend`
  - `frontend`
  - `.gitignore`
  - `setup.sh`
  - `update_luna_tone_and_white_theme.py`

At the time of review, the repository is structured as a frontend/backend MVP rather than a documentation-heavy product repository.

There is no clear `docs` folder visible from the repository root yet. These documents are intended to become the initial product documentation set under `docs/`.

## 3. Current Technical Structure

### 3.1 Backend

The backend is organized under `backend/app`.

Observed structure:

- `backend/app/db`
- `backend/app/models`
- `backend/app/services`
- `backend/app/__init__.py`
- `backend/app/legacy_api.py`
- `backend/app/main.py`

The current backend appears to be centered around `legacy_api.py`.

Important backend responsibilities currently visible:

- FastAPI app
- `/health` endpoint
- `/api/analyze` endpoint
- ticker/instrument resolution
- Korean and US stock support
- price data fetching
- chart/price analysis
- personalization logic
- AI opinion generation
- fallback AI opinion handling
- holder/viewer behavior prompt control
- profit-zone logic
- mode-specific forbidden phrase filtering

The backend app title currently indicates an older framing:

> `Luna Stock Chart Tutor API`

This title reflects the older “chart tutor / chart explanation” framing and should eventually be renamed to match the AI trading coach direction.

### 3.2 Backend Services

Observed backend service files:

- `backend/app/services/chart_renderer.py`
- `backend/app/services/stock_master.py`

The services layer currently supports:

- chart image rendering
- stock master / instrument lookup

This is a useful foundation, but product logic still appears concentrated in `legacy_api.py`.

### 3.3 Backend Tests

Observed backend test file:

- `backend/tests/test_realtime_summary.py`

Current test coverage appears narrow relative to the product quality needs of PROJECTLUNA.

The most important missing QA coverage is not only technical correctness, but coaching quality:

- holder/viewer separation
- profit-zone guidance
- fallback response quality
- conclusion-first structure
- actionability
- psychological coaching
- avoidance of generic chart narration

### 3.4 Frontend

The frontend is organized under `frontend/app` and `frontend/components`.

Observed `frontend/app` structure:

- `frontend/app/api/proxy-analyze`
- `frontend/app/result`
- `frontend/app/layout.js`
- `frontend/app/page.js`

Observed `frontend/components` structure:

- `frontend/components/CandleChart.js`
- `frontend/components/ResultClient.js`

The frontend currently supports a basic MVP flow:

1. User enters a stock name or ticker.
2. User selects market hint: auto, Korea, US.
3. User selects holder/viewer mode.
4. User selects investment style.
5. If holder mode is selected, user enters average price and quantity.
6. Frontend sends request through `api/proxy-analyze`.
7. Backend returns chart analysis, personalization, state hint, and AI opinion.
8. Result screen displays chart, technical summary, and LUNA commentary.

## 4. Current User Flow

### 4.1 Input Screen

The current input screen is still framed as:

> 루나 차트 해설 MVP

This is a product-positioning problem.

Even though backend logic is already moving toward coaching, the frontend still introduces the product as a chart explanation MVP.

Current input fields include:

- stock search
- market selection: auto / Korea / US
- holder/viewer mode
- investment style
- average price for holders
- quantity for holders

This is directionally correct because it collects the minimum context needed to separate holder and viewer decisions.

### 4.2 Result Screen

The result screen currently includes:

- loading state with LUNA character tone
- candle chart
- current price
- state hint
- technical summary
- LUNA commentary bottom sheet

Current UI labels still include:

- `기술 요약`
- `루나 해설 보기`
- `루나 해설`

These labels are not wrong, but they understate PROJECTLUNA's intended value. The product should move toward labels such as:

- `LUNA 판단`
- `지금 할 일`
- `보유자 대응`
- `관망자 대응`
- `수익 보호 체크`
- `기다릴 조건`

## 5. Current Backend Product Logic

The backend already contains several product-aligned elements.

### 5.1 Holder and Viewer Mode

The `/api/analyze` endpoint accepts:

- `ticker`
- `mode`
- `avg_price`
- `quantity`
- `style`
- `market_hint`

The `mode` is validated as either:

- `viewer`
- `holder`

For holder mode, average price and quantity are required.

This is highly aligned with PROJECTLUNA's core philosophy because holder and viewer decisions should not be mixed.

### 5.2 Investment Style

The backend currently includes styles such as:

- conservative
- pullback
- trend
- swing
- protect_profit
- trend_partial

This is useful, but should remain secondary to the user's current position state.

Style should modify guidance tone and risk posture, not override the core decision logic.

### 5.3 Profit-Zone Awareness

The backend includes logic for profit-zone handling.

The current direction already recognizes that holder users in profit require different guidance than generic holders.

This is one of the most important product assets in the current implementation.

For PROJECTLUNA, a profit-zone holder should not be treated as a generic “hold or sell” user. The correct framing is:

> protect profit first, then consider upside.

### 5.4 Prompt Guardrails

The backend prompt already contains important behavior rules:

- holder and viewer should not be mixed
- viewer should focus on entry timing
- holder should focus on position management
- profit-zone should prioritize profit protection
- resistance / extension should trigger decision-zone framing
- final answer should end with a single action conclusion
- internal field names should not be exposed

This is directionally excellent.

However, the product surface has not fully caught up with this backend intent.

## 6. Current Product Gap

The current implementation is stronger in backend intent than frontend positioning.

### What is already aligned

- holder/viewer mode exists
- holder inputs exist
- investment style exists
- backend has behavior guardrails
- profit-zone logic exists
- fallback opinion exists
- result page has LUNA character tone
- chart and AI commentary are integrated

### What is not yet aligned

- homepage still says chart explanation MVP
- result page foregrounds technical summary
- LUNA guidance is in a bottom sheet rather than the main decision surface
- current UI does not strongly show conclusion → reason → action
- action coaching is not yet visually separated
- QA coverage does not yet reflect product philosophy
- documentation does not yet anchor product decisions
- PC dashboard direction is not yet visible in the current UI

## 7. Product Interpretation

The repository currently represents a working MVP of an AI-assisted stock chart analysis service with early trading coach logic.

The next product step should not be broad feature expansion.

The next step should be to make the existing flow feel unmistakably like an AI trading coach.

That means:

- rename product framing away from chart explanation
- restructure result screen around decisions
- make holder/viewer separation visible in UI
- make profit-zone guidance more prominent
- make fallback responses useful rather than generic
- QA every response against coaching principles
- move product rules from implicit prompt behavior into explicit product documentation

## 8. Source References

Repository and implementation references checked:

- Repository root: https://github.com/tigger0721-hub/PROJECTLUNA
- Backend app: https://github.com/tigger0721-hub/PROJECTLUNA/tree/main/backend/app
- Backend services: https://github.com/tigger0721-hub/PROJECTLUNA/tree/main/backend/app/services
- Backend tests: https://github.com/tigger0721-hub/PROJECTLUNA/tree/main/backend/tests
- Frontend app: https://github.com/tigger0721-hub/PROJECTLUNA/tree/main/frontend/app
- Frontend components: https://github.com/tigger0721-hub/PROJECTLUNA/tree/main/frontend/components
- Frontend home page: https://github.com/tigger0721-hub/PROJECTLUNA/blob/main/frontend/app/page.js
- Result client: https://github.com/tigger0721-hub/PROJECTLUNA/blob/main/frontend/components/ResultClient.js
- Proxy analyze route: https://github.com/tigger0721-hub/PROJECTLUNA/blob/main/frontend/app/api/proxy-analyze/route.js
- Backend legacy API: https://github.com/tigger0721-hub/PROJECTLUNA/blob/main/backend/app/legacy_api.py

## Last Updated

2026-06-18 KST

## Version

v0.1

## Owner

PROJECTLUNA PM
