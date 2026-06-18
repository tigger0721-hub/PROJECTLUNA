# PROJECTLUNA Roadmap

## 1. Roadmap Principle

PROJECTLUNA should grow from a chart analysis MVP into an AI trading coach platform.

The roadmap must protect the product philosophy:

> decision support first, feature expansion second.

A feature should be prioritized only if it helps users make better trading decisions, avoid impulsive behavior, or return daily with a clear reason.

## 2. Current Stage

PROJECTLUNA currently has a working MVP flow:

- stock input
- market selection
- holder/viewer mode
- investment style
- holder average price and quantity
- chart analysis
- AI opinion
- result screen
- LUNA character tone
- backend guardrails for holder/viewer and profit-zone behavior

The next roadmap step is not to add many new surfaces.

The next step is to make the existing flow unmistakably useful as a trading coach.

## 3. Roadmap Overview

| Stage | Theme | Product Goal |
|---|---|---|
| Now | Decision Quality | Make the current MVP behave like an AI trading coach |
| Next | Daily Use | Create reasons to use LUNA every trading day |
| Later | Personalization | Use portfolio, watchlist, and behavior history |
| Future | Real-Time Partner | Become an active investment companion |

## 4. Now: Decision Quality

Timeframe: immediate

Priority: highest

### 4.1 Reframe Product Language

Current issue:

- product still appears as a chart explanation MVP

Required direction:

- reposition as AI trading coach

Key work:

- homepage title and subtitle
- result page labels
- loading messages
- CTA wording
- response section names

Target language:

- LUNA 트레이딩 코치
- 오늘의 판단
- 지금 할 일
- 기다릴 조건
- 수익 보호 기준
- 관망자 판단
- 보유자 대응

### 4.2 Strengthen Response Structure

Required response structure:

1. conclusion
2. reason
3. action

Every response should answer:

- what is the decision?
- why?
- what should the user do now?

### 4.3 Holder/Viewer Separation

Current backend direction is good.

Next product step:

- make separation visible in result UI
- ensure QA catches mixed responses
- avoid shared generic commentary
- make holder response position-management-first
- make viewer response entry-timing-first

### 4.4 Profit-Zone Upgrade

Profit-zone handling is a core differentiator.

Required behavior:

- profit protection first
- partial profit when appropriate
- tighter protection near resistance
- avoid greedy holding language
- avoid additional buying encouragement when extended

### 4.5 Fallback Upgrade

Fallback should be useful, not just apologetic.

Fallback should include:

- uncertainty reason
- conservative decision
- wait condition
- re-check trigger
- what not to do

### 4.6 QA Criteria

Build a repeatable response QA set.

Core QA scenarios:

- viewer near resistance
- viewer after sharp rise
- viewer near support
- holder in profit near resistance
- holder in profit after extension
- holder in loss below support
- sideways / unclear chart
- data insufficient
- AI opinion fallback
- Korean stock input
- US ticker input

## 5. Next: Daily Use

Timeframe: after Decision Quality is stable

Priority: high

### 5.1 Watchlist Foundation

Goal:

- users should not need to manually restart from zero every time

Minimum scope:

- saved stocks
- last LUNA decision
- last checked price
- current state hint
- re-check condition

Not needed yet:

- complex alerts
- brokerage integration
- social sharing

### 5.2 Daily LUNA Briefing

Goal:

- create a reason to open LUNA daily

Minimum briefing structure:

- stocks that need attention today
- stocks to avoid chasing
- stocks near decision zones
- profit-zone positions needing protection
- unclear setups to ignore

The briefing should not become market news commentary.

It should answer:

> what should the user pay attention to today?

### 5.3 Result History

Goal:

- let users see how LUNA’s judgment changed over time

Minimum scope:

- previous analysis result
- previous decision
- previous key level
- previous re-check condition

Useful for:

- building trust
- reducing impulsive repeated checking
- helping users learn timing

## 6. Later: Personalization

Timeframe: after Daily Use foundation

Priority: medium

### 6.1 Portfolio-Based Analysis

Goal:

- make LUNA more personal and more useful for holders

Potential inputs:

- owned stocks
- average price
- quantity
- unrealized P/L
- position size
- sector concentration

Coaching outputs:

- protect profit
- reduce risk
- avoid overexposure
- identify emotional holding
- position-level action plan

### 6.2 Investment Habit Analysis

Goal:

- help users improve behavior over time

Possible habit patterns:

- chasing after sharp rise
- averaging down too quickly
- selling winners too early
- holding losers too long
- ignoring pre-defined invalidation conditions

This should be coaching-oriented, not judgmental.

### 6.3 Combined News + Chart Analysis

Goal:

- add context when it changes the decision

Constraint:

- news must not dominate the product
- chart + position + psychology remains the core
- news should explain why risk or timing changed

## 7. Future: Real-Time Investment Partner

Timeframe: long-term

Priority: future

### 7.1 Chat-Based Investment Coach

Goal:

- allow users to ask follow-up questions

Examples:

- “If I already have 30% profit, should I reduce?”
- “What would make this setup invalid?”
- “Am I chasing here?”
- “What should I wait for tomorrow?”

Chat must preserve the product philosophy.

It should not become long market commentary.

### 7.2 AI Character Interface

Goal:

- make LUNA feel like a consistent coach

Constraint:

- character should support decision clarity
- character should not become the main product
- cuteness must not reduce trust or actionability

### 7.3 Real-Time Partner

Goal:

- help users during market hours

Potential features:

- decision-zone alerts
- profit-protection reminders
- chase-risk warnings
- re-check condition notifications

This should be built only after decision quality is reliable.

## 8. Explicitly Deprioritized

The following should not be prioritized now:

- generic indicator education
- long-form technical reports
- automatic buy/sell signal service
- social feed
- community ranking
- leaderboard
- complex portfolio analytics before decision quality
- news-heavy dashboard
- character animation before coaching clarity

## 9. Roadmap Decision Rules

Use these questions before prioritizing any feature:

1. Does this help trading judgment?
2. Does this reduce impulsive behavior?
3. Does this improve timing?
4. Does this separate holder and viewer needs?
5. Does this strengthen daily use?
6. Does this differentiate LUNA from chart tools?
7. Is this necessary now?

If the answer is no, defer the feature.

## 10. Current Recommended Order

1. Rename and reposition visible UI language.
2. Move LUNA decision above technical summary.
3. Enforce conclusion → reason → action.
4. Strengthen holder/viewer UI separation.
5. Improve profit-zone response quality.
6. Improve fallback response quality.
7. Build QA scenarios.
8. Add minimal watchlist.
9. Add daily briefing.
10. Add history.
11. Add portfolio-based coaching.
12. Add habit analysis.
13. Add news context.
14. Add chat coach.
15. Add real-time partner features.

## Last Updated

2026-06-18 KST

## Version

v0.1

## Owner

PROJECTLUNA PM
