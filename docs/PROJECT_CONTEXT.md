# PROJECTLUNA Project Context

## 1. Document Role

This document records the current product and implementation context as of 2026-06-18.

Its role is to help contributors understand the current PROJECTLUNA implementation, the product direction already visible in the codebase, and the gaps that remain between the MVP and the intended AI trading coach experience.

This document is intentionally focused on current state and gap analysis.

Related documents:

- `PRD.md`: V1 requirements and acceptance criteria
- `ROADMAP.md`: priorities and staged development direction
- `LUNA_PHILOSOPHY.md`: stable product philosophy and response principles
- `QA_CRITERIA.md`: release gate and response-quality test scenarios

The docs folder contains the product documentation baseline for PROJECTLUNA.

## 2. Product Context

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

## 3. Repository State

Repository checked:

- GitHub repository: https://github.com/tigger0721-hub/PROJECTLUNA
- Branch observed for this context: `main`
- Repository visibility: public
- Current top-level structure:
  - `backend`
  - `frontend`
  - `docs`
  - `.gitignore`
  - `setup.sh`
  - `update_luna_tone_and_white_theme.py`

The repository is structured as a frontend/backend MVP with a product documentation baseline under `docs/`.

## 4. Current Technical Structure

### 4.1 Backend

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
- ticker and instrument resolution
- Korean and US stock support
- price data fetching
- chart and price analysis
- personalization logic
- AI opinion generation
- fallback AI opinion handling
- holder/viewer behavior prompt control
- profit-zone logic
- mode-specific forbidden phrase filtering

The backend app title currently indicates an older framing:

> `Luna Stock Chart Tutor API`

This title reflects the older chart tutor / chart explanation framing and should eventually be renamed to match the AI trading coach direction.

### 4.2 Backend Services

Observed backend service files:

- `backend/app/services/chart_renderer.py`
- `backend/app/services/stock_master.py`

The services layer currently supports:

- chart image rendering
- stock master / instrument lookup

This is a useful foundation, but product logic still appears concentrated in `legacy_api.py`.

### 4.3 Backend Tests

Observed backend test file:

- `backend/tests/test_realtime_summary.py`

Current test coverage appears narrow relative to PROJECTLUNA's product quality needs.

The most important missing QA coverage is not only technical correctness, but coaching quality:

- holder/viewer separation
- profit-zone guidance
- fallback response quality
- conclusion-first structure
- actionability
- psychology-aware coaching
- avoidance of generic chart narration
- re-check condition quality

### 4.4 Frontend

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

## 5. Current User Flow

### 5.1 Input Screen

The current input screen is still framed as:

> 루나 차트 해설 MVP

This is a product-positioning gap.

Even though backend logic is already moving toward coaching, the frontend still introduces the product as a chart explanation MVP.

Current input fields include:

- stock search
- market selection: auto / Korea / US
- holder/viewer mode
- investment style
- average price for holders
- quantity for holders

This is directionally correct because it collects the minimum context needed to separate holder and viewer decisions.

### 5.2 Result Screen

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
- `다시 볼 조건`

## 6. Current Backend Product Logic

The backend already contains several product-aligned elements.

### 6.1 Holder and Viewer Mode

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

This is aligned with PROJECTLUNA's core philosophy because holder and viewer decisions should not be mixed.

### 6.2 Investment Style

The backend currently includes styles such as:

- conservative
- pullback
- trend
- swing
- protect_profit
- trend_partial

This is useful, but should remain secondary to the user's current position state.

Style should modify guidance tone and risk posture, not override the core decision logic.

### 6.3 Profit-Zone Awareness

The backend includes logic for profit-zone handling.

The current direction already recognizes that holder users in profit require different guidance than generic holders.

For PROJECTLUNA, a profit-zone holder should not be treated as a generic hold-or-sell user. The correct framing is:

> protect profit first, then consider upside.

### 6.4 Prompt Guardrails

The backend prompt already contains important behavior rules:

- holder and viewer should not be mixed
- viewer should focus on entry timing
- holder should focus on position management
- profit-zone should prioritize profit protection
- resistance or extension should trigger decision-zone framing
- internal field names should not be exposed

The default response structure should be:

1. Conclusion
2. Reason
3. Action
4. Re-check Condition

In user-facing Korean, this maps to:

1. 결론
2. 이유
3. 행동
4. 다시 볼 조건

## 7. Current Product Gap

The current implementation is stronger in backend intent than frontend positioning.

Already aligned:

- holder/viewer mode exists
- holder inputs exist
- investment style exists
- backend has behavior guardrails
- profit-zone logic exists
- fallback opinion exists
- result page has LUNA character tone
- chart and AI commentary are integrated

Not yet fully aligned:

- homepage still says chart explanation MVP
- result page foregrounds technical summary
- LUNA guidance is in a bottom sheet rather than the main decision surface
- current UI does not strongly show conclusion, reason, action, and re-check condition
- action coaching is not yet visually separated
- QA coverage does not yet reflect product philosophy
- PC dashboard direction is not yet visible in the current UI

## 8. Product Interpretation

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
- make product rules explicit in documentation and tests

## 9. Source References

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

v0.2

## Owner

PROJECTLUNA PM
