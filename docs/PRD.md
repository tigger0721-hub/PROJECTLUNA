# PROJECTLUNA PRD

## 1. Document Role

This document defines PROJECTLUNA V1 product requirements and acceptance criteria.

It answers what V1 should build, why it matters, and what must be true for a requirement to be considered complete.

This document should not replace:

- `PROJECT_CONTEXT.md` for current implementation state and gap analysis
- `ROADMAP.md` for sequencing and priority stages
- `LUNA_PHILOSOPHY.md` for stable product principles
- `QA_CRITERIA.md` for release gates and scenario tests

## 2. Product Summary

PROJECTLUNA is an AI trading coach.

It helps users make better trading decisions by combining chart context, user position state, risk management, and psychology-aware guidance.

The product is not designed to be a generic chart explanation tool.

The core output should help users decide:

- whether to enter now
- whether to wait
- whether to avoid chasing
- whether to hold
- whether to reduce exposure
- whether to protect profit
- whether risk management matters more than upside
- what condition should trigger a re-check

## 3. Current Product Stage

PROJECTLUNA is currently in MVP stage.

The current repository already includes:

- frontend input screen
- holder/viewer mode selection
- investment style selection
- holder average price and quantity inputs
- Next.js proxy route
- FastAPI backend
- `/api/analyze` endpoint
- Korean and US market support
- chart analysis
- AI commentary generation
- LUNA character-style loading and commentary
- mode-specific backend prompt guardrails
- profit-zone handling
- fallback AI opinion handling

However, the current product still carries chart explanation framing in visible UI and naming.

The PRD priority is therefore not to add many new features.

The priority is to align the existing MVP with the AI trading coach product direction.

## 4. Product Principles for V1

PROJECTLUNA V1 must follow these principles:

1. LUNA is not an AI that explains charts.
2. LUNA helps users make trading decisions.
3. Every response should follow conclusion -> reason -> action -> re-check condition.
4. Holder and viewer situations must be separated.
5. Holder users need position management.
6. Viewer users need entry timing judgment.
7. Profit-zone holders need profit protection first.
8. Psychology matters more than indicator narration.
9. Practical response beats abstract explanation.
10. The product should prevent impulsive trading.
11. LUNA should communicate uncertainty through conditions, not false certainty.

In user-facing Korean, the default response structure is:

1. 결론
2. 이유
3. 행동
4. 다시 볼 조건

## 5. Target Users

### 5.1 Viewer

A viewer does not currently hold the stock.

Their core questions are:

- Is now a good entry point?
- Should I wait?
- Is this chasing?
- What price action should I wait for?
- If I enter, should the size be small?
- When should I avoid the setup?
- When should I re-check?

Viewer guidance must focus on entry timing.

Viewer guidance must not use holder language such as:

- 손절
- 익절
- 비중 축소
- 물량 정리
- 포지션 정리
- 보유 물량 관리
- 부분 익절
- 수익 보호

### 5.2 Holder

A holder already owns the stock.

Their core questions are:

- Should I keep holding?
- Should I reduce?
- Should I protect profit?
- Should I avoid adding more?
- What level invalidates the hold?
- Am I holding because of hope, fear, or greed?
- What condition should I watch next?

Holder guidance must focus on position management.

Holder guidance must not be written as if the user is making a first entry.

Holder guidance must avoid viewer-first phrases such as:

- 첫 진입
- 신규 진입 대기
- 들어가보자
- 관망자 기준
- 신규 매수자 기준

### 5.3 Profit-Zone Holder

A profit-zone holder is a holder with meaningful unrealized profit.

Their core questions are:

- Should I protect gains?
- Should I partially take profit?
- Should I trail the position?
- Am I being greedy?
- What condition tells me the trend is weakening?

Profit-zone guidance must prioritize profit protection.

The default framing is:

> protect profit first, then consider further upside.

### 5.4 Loss-Zone Holder

A loss-zone holder is a holder with meaningful unrealized loss.

Their core questions are:

- Is this still recoverable?
- Should I stop adding?
- Should I cut risk?
- Am I averaging down emotionally?
- What level makes the trade invalid?

Loss-zone guidance must prioritize damage control.

## 6. Current User Flow

### 6.1 Input

Current user input includes:

- stock name or ticker
- market hint
- holder/viewer mode
- investment style
- average price for holder mode
- quantity for holder mode

This is the correct minimum input set for the current product stage.

### 6.2 Analysis Request

The frontend sends the analysis request through a proxy route to the backend.

The backend receives the request through `/api/analyze`.

The backend then:

1. validates mode and style
2. resolves the instrument
3. fetches price data
4. builds chart analysis
5. applies realtime quote data when available
6. builds personalization
7. generates AI opinion
8. falls back if AI opinion fails
9. returns analysis, personalization, state hint, and AI opinion

### 6.3 Result

The current result screen shows:

- stock/ticker
- user mode and style
- current price
- state hint
- technical summary
- LUNA commentary

This should evolve so the first visible output is not technical summary, but decision guidance.

## 7. V1 Product Goal

The V1 goal is:

> Make PROJECTLUNA feel like an AI trading coach, not a chart explanation MVP.

This means the product must clearly answer:

- What is LUNA's decision?
- Why is that the decision?
- What should the user do next?
- What condition should the user re-check?
- Does the answer differ for holder and viewer?
- Does the answer account for user psychology?
- Does the answer prevent impulsive behavior?

## 8. V1 Non-Goals

The following are not V1 priorities:

- full portfolio integration
- brokerage account connection
- real-time trading execution
- news aggregation
- social features
- community features
- advanced technical indicator education
- long-form market commentary
- automatic buy/sell signal product
- character-first entertainment experience

These may become useful later, but they should not distract from the current quality priority.

## 9. Safety and Trust Requirements

LUNA must preserve user trust and avoid overclaiming.

Requirements:

- LUNA does not promise guaranteed profit.
- LUNA does not speak like an unconditional buy or sell signal.
- LUNA does not make definitive statements as if providing regulated investment advice.
- If uncertainty is high, LUNA explains the condition and re-check standard instead of pretending certainty.
- Excessive confidence, excessive trading encouragement, and fear-driven wording are prohibited.
- LUNA should guide better decision-making, not push the user into more trades.

Acceptance criteria:

- Responses avoid guaranteed-outcome wording.
- Responses avoid unconditional buy/sell framing.
- Unclear charts include a wait or re-check condition.
- Risk language is protective and practical, not fear-inducing.

Priority: P0

## 10. Core Requirements

### R1. Reposition Product Language

Current visible product framing should move away from chart explanation.

Replace product framing such as:

- 루나 차트 해설 MVP
- 기술 요약
- 루나 해설 보기

With decision-oriented language such as:

- LUNA 트레이딩 코치
- 오늘의 판단
- 지금 할 일
- 보유자 대응
- 관망자 대응
- 수익 보호 체크
- 다시 볼 조건

Acceptance criteria:

- The first screen describes LUNA as a trading coach.
- The result screen foregrounds decision guidance.
- Chart explanation is supporting evidence, not the main product promise.

Priority: P0

### R2. Enforce Conclusion -> Reason -> Action -> Re-check Condition

Every AI response must follow this structure:

1. Conclusion
2. Reason
3. Action
4. Re-check Condition

Example structure:

```text
결론: 지금은 추격 진입보다 기다리는 쪽이 좋아.
이유: 최근 상승 이후 저항 근처라 보상보다 리스크가 커졌어.
행동: 지금은 매수하지 말고 눌림을 기다리자.
다시 볼 조건: 눌림 후 지지가 확인되거나 저항 돌파 후 안착하면 다시 보자.
```

Acceptance criteria:

- summary contains clear decision framing
- commentary explains why
- commentary includes one practical action
- commentary includes a concrete re-check condition
- final guidance does not end with vague language only

Priority: P0

### R3. Separate Holder and Viewer Guidance

Holder and viewer guidance must not be mixed.

Viewer response should answer:

- enter now?
- wait?
- avoid chasing?
- enter on pullback?
- what invalidates entry?
- what condition should trigger a re-check?

Holder response should answer:

- hold?
- reduce?
- protect profit?
- cut risk?
- avoid adding?
- what invalidates holding?
- what condition should trigger a re-check?

Acceptance criteria:

- viewer response does not mention holder-specific language
- holder response does not suggest first-entry logic
- UI clearly displays the selected user state
- response structure changes based on selected mode

Priority: P0

### R4. Improve Profit-Zone Response

Profit-zone holders must receive profit-protection-first guidance.

When a holder is in profit, LUNA should not simply say hold if trend is strong.

LUNA should consider:

- resistance proximity
- recent extension
- profit giveback risk
- partial profit
- trailing protection
- emotional greed
- avoiding late additional buying
- re-check condition for trend weakening

Acceptance criteria:

- profit-zone response mentions profit protection
- if near resistance or extended, partial profit or tighter protection is considered
- response does not focus only on downside stop-loss
- response does not encourage blind holding
- response gives a condition for re-checking the remaining position

Priority: P0

### R5. Improve Fallback Response

Fallback should not feel like system failure.

Fallback should still coach the user.

A good fallback should include:

- uncertainty reason
- what not to do now
- what condition to wait for
- when to retry or re-check
- conservative action

Acceptance criteria:

- fallback never gives fake certainty
- fallback gives a useful waiting condition
- fallback does not become generic apology text
- fallback keeps LUNA's coaching tone
- fallback includes a re-check condition

Priority: P0

### R6. Add Psychology-Based Coaching Layer

LUNA should explicitly identify trading psychology when relevant.

Examples:

- FOMO after a sharp rise
- fear after a pullback
- greed in profit-zone
- hope-based holding in loss-zone
- revenge buying after loss
- overconfidence after short-term gains

Acceptance criteria:

- response includes one behavior warning when relevant
- warning is practical, not moralizing
- psychology note leads to action or a re-check condition
- no generic be careful phrasing without concrete behavior

Priority: P1

### R7. Result Screen Should Become Decision Surface

The result screen should prioritize decisions over indicators.

Recommended result structure:

1. LUNA decision
2. User mode: holder or viewer
3. Current action
4. Why
5. Re-check condition
6. Risk condition
7. Chart evidence
8. Detailed commentary

Acceptance criteria:

- decision appears before technical summary
- chart remains visible but does not dominate the decision
- action guidance is readable without opening a hidden panel
- re-check condition is visible without opening a hidden panel
- bottom sheet may remain, but the main decision should not be hidden inside it

Priority: P1

### R8. QA Criteria Must Become Product Gate

The product should not ship analysis changes without QA review.

Acceptance criteria:

- response samples are reviewed across core scenarios
- holder/viewer confusion is treated as a blocking issue
- profit-zone failure is treated as a blocking issue
- vague conclusion is treated as a blocking issue
- missing re-check condition is treated as a quality failure
- generic indicator narration is treated as a quality failure

Priority: P0

## 11. Internal Action Labels and User Copy

English action labels are internal enum examples only. They should not be shown to users as the main copy.

| Internal label | User-facing Korean copy |
|---|---|
| `WAIT` | 기다리자 |
| `AVOID_CHASING` | 추격하지 말자 |
| `ENTER_ON_PULLBACK` | 눌림 확인 후 접근하자 |
| `HOLD_WITH_PROTECTION` | 보유하되 보호 기준을 올리자 |
| `TAKE_PARTIAL_PROFIT` | 일부 수익을 보호하자 |
| `CUT_RISK` | 리스크를 줄이자 |

Acceptance criteria:

- Internal labels may appear in code, tests, or docs as enum examples.
- User-visible UI and AI copy should use Korean decision wording.
- English labels should not replace user-facing coaching sentences.

## 12. Success Metrics

### Decision Clarity

Target:

- user can identify LUNA's recommendation within 5 seconds

### Holder/Viewer Separation

Target:

- zero critical holder/viewer mixing in QA samples

### Profit-Zone Quality

Target:

- every profit-zone response includes protection logic

### Re-check Quality

Target:

- every response gives a concrete condition for when to look again

### Fallback Trust

Target:

- fallback includes wait condition and re-check trigger

### Daily Use Potential

Target:

- user can save or remember a clear re-check condition

## 13. Product Decision

V1 should focus on explanation quality and decision coaching.

Do not prioritize broad feature expansion until the existing MVP consistently behaves like an AI trading coach.

The correct next product milestone is:

> LUNA Decision Quality v1

## Last Updated

2026-06-18 KST

## Version

v0.2

## Owner

PROJECTLUNA PM
