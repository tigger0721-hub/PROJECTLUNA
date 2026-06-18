# PROJECTLUNA PRD

## 1. Product Summary

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

## 2. Current Product Stage

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

## 3. Product Philosophy

PROJECTLUNA must follow these principles:

1. LUNA is not an AI that explains charts.
2. LUNA helps users make trading decisions.
3. Every response should follow conclusion → reason → action.
4. Holder and viewer situations must be separated.
5. Holder users need position management.
6. Viewer users need entry timing judgment.
7. Profit-zone holders need profit protection first.
8. Psychology matters more than indicator narration.
9. Practical response beats abstract explanation.
10. The product should prevent impulsive trading.

## 4. Target Users

### 4.1 Viewer

A viewer does not currently hold the stock.

Their core questions are:

- Is now a good entry point?
- Should I wait?
- Is this chasing?
- What price action should I wait for?
- If I enter, should the size be small?
- When should I avoid the setup?

Viewer guidance must focus on entry timing.

Viewer guidance must not use holder language such as:

- 손절
- 익절
- 보유 물량
- 포지션 유지
- 비중 축소
- 부분 익절

### 4.2 Holder

A holder already owns the stock.

Their core questions are:

- Should I keep holding?
- Should I reduce?
- Should I protect profit?
- Should I avoid adding more?
- What level invalidates the hold?
- Am I holding because of hope, fear, or greed?

Holder guidance must focus on position management.

Holder guidance must not be written as if the user is making a first entry.

### 4.3 Profit-Zone Holder

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

### 4.4 Loss-Zone Holder

A loss-zone holder is a holder with meaningful unrealized loss.

Their core questions are:

- Is this still recoverable?
- Should I stop adding?
- Should I cut risk?
- Am I averaging down emotionally?
- What level makes the trade invalid?

Loss-zone guidance must prioritize damage control.

## 5. Current User Flow

### 5.1 Input

Current user input includes:

- stock name or ticker
- market hint
- holder/viewer mode
- investment style
- average price for holder mode
- quantity for holder mode

This is the correct minimum input set for the current product stage.

### 5.2 Analysis Request

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

### 5.3 Result

The current result screen shows:

- stock/ticker
- user mode and style
- current price
- state hint
- technical summary
- LUNA commentary

This should evolve so the first visible output is not technical summary, but decision guidance.

## 6. V1 Product Goal

The v1 goal is:

> Make PROJECTLUNA feel like an AI trading coach, not a chart explanation MVP.

This means the product must clearly answer:

- What is LUNA’s decision?
- Why is that the decision?
- What should the user do next?
- Does the answer differ for holder and viewer?
- Does the answer account for user psychology?
- Does the answer prevent impulsive behavior?

## 7. V1 Non-Goals

The following are not v1 priorities:

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

## 8. Core Requirements

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
- 기다릴 조건

Acceptance criteria:

- The first screen describes LUNA as a trading coach.
- The result screen foregrounds decision guidance.
- Chart explanation is supporting evidence, not the main product promise.

Priority: P0

### R2. Enforce Conclusion → Reason → Action

Every AI response must follow this structure:

1. Conclusion
2. Reason
3. Action

Example structure:

```text
결론: 지금은 추격 진입보다 기다리는 쪽이 좋아.
이유: 최근 상승 이후 저항 근처라 보상보다 리스크가 커졌어.
행동: 눌림이 나오고 지지가 확인될 때만 소액으로 접근해.
````

Acceptance criteria:

* summary contains clear decision framing
* commentary explains why
* final sentence ends with a single action conclusion
* no response ends with vague language only

Priority: P0

### R3. Separate Holder and Viewer Guidance

Holder and viewer guidance must not be mixed.

Viewer response should answer:

* enter now?
* wait?
* avoid chasing?
* enter on pullback?
* what invalidates entry?

Holder response should answer:

* hold?
* reduce?
* protect profit?
* cut loss?
* avoid adding?
* what invalidates holding?

Acceptance criteria:

* viewer response does not mention holder-specific language
* holder response does not suggest first-entry logic
* UI clearly displays the selected user state
* response structure changes based on selected mode

Priority: P0

### R4. Improve Profit-Zone Response

Profit-zone holders must receive profit-protection-first guidance.

When a holder is in profit, LUNA should not simply say “hold if trend is strong.”

LUNA should consider:

* resistance proximity
* recent extension
* profit giveback risk
* partial profit
* trailing protection
* emotional greed
* avoiding late additional buying

Acceptance criteria:

* profit-zone response mentions profit protection
* if near resistance or extended, partial profit or tighter protection is considered
* response does not focus only on downside stop-loss
* response does not encourage blind holding

Priority: P0

### R5. Improve Fallback Response

Fallback should not feel like system failure.

Fallback should still coach the user.

A good fallback should include:

* uncertainty reason
* what not to do now
* what condition to wait for
* when to retry or re-check
* conservative action

Acceptance criteria:

* fallback never gives fake certainty
* fallback gives a useful waiting condition
* fallback does not become generic apology text
* fallback keeps LUNA’s coaching tone

Priority: P0

### R6. Add Psychology-Based Coaching Layer

LUNA should explicitly identify trading psychology when relevant.

Examples:

* FOMO after a sharp rise
* fear after a pullback
* greed in profit-zone
* hope-based holding in loss-zone
* revenge buying after loss
* overconfidence after short-term gains

Acceptance criteria:

* response includes one behavior warning when relevant
* warning is practical, not moralizing
* psychology note leads to action
* no generic “be careful” phrasing without concrete behavior

Priority: P1

### R7. Result Screen Should Become Decision Surface

The result screen should prioritize decisions over indicators.

Recommended result structure:

1. LUNA decision
2. User mode: holder or viewer
3. Current action
4. Why
5. Risk condition
6. Chart evidence
7. Detailed commentary

Acceptance criteria:

* decision appears before technical summary
* chart remains visible but does not dominate the decision
* action guidance is readable without opening a hidden panel
* bottom sheet may remain, but the main decision should not be hidden inside it

Priority: P1

### R8. QA Criteria Must Become Product Gate

The product should not ship analysis changes without QA review.

Acceptance criteria:

* response samples are reviewed across core scenarios
* holder/viewer confusion is treated as a blocking issue
* profit-zone failure is treated as a blocking issue
* vague conclusion is treated as a blocking issue
* generic indicator narration is treated as a quality failure

Priority: P0

## 9. Success Metrics

### Decision Clarity

Measures whether the user can understand what to do next.

Target:

* user can identify LUNA’s recommendation within 5 seconds

### Holder/Viewer Separation

Measures whether guidance is appropriate to user state.

Target:

* zero critical holder/viewer mixing in QA samples

### Profit-Zone Quality

Measures whether profitable holders receive profit-protection guidance.

Target:

* every profit-zone response includes protection logic

### Fallback Trust

Measures whether fallback responses remain useful.

Target:

* fallback includes wait condition and re-check trigger

### Daily Use Potential

Measures whether the product gives users a reason to return.

Target:

* user can save or remember a clear re-check condition

## 10. Product Decision

V1 should focus on explanation quality and decision coaching.

Do not prioritize broad feature expansion until the existing MVP consistently behaves like an AI trading coach.

The correct next product milestone is:

> LUNA Decision Quality v1

## Last Updated

2026-06-18 KST

## Version

v0.1

## Owner

PROJECTLUNA PM
