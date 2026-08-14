# HACKER GenAI+ — Comprehensive Build Plan

> AI Trading Assistant · Telegram Python Bot
> Repo: `KKPROJECT69/kkproject69` · Branch: `arena/019ffefd-kkproject69`

---

## 0. North Star (one paragraph)

HACKER GenAI+ is a modular, premium **AI Trading Assistant** that consumes market
candles + economic-news context → normalizes them → runs market analysis →
evaluates **11 strategies** → passes evidence to an **AI decision layer** →
applies **confidence / risk / payout / news filters** → produces a
**CALL / PUT / NO_TRADE** decision → delivers branded signals to a **private
Telegram channel** with **15–20s pre-candle timing** → tracks **DIRECT WIN /
MTG WIN / BREAK-EVEN / LOSS** outcomes → runs **AI loss reviews** and **learning**
→ provides **paper trading**, **reports**, and **premium/VIP** access →
runs **24/7 in the cloud** with per-user isolation.

**Hard boundary (non-negotiable):** automatic broker execution / real-money
order placement is **OUT OF SCOPE**. This is a signal & analysis platform.

---

## 1. Non-Negotiable Rules (encoded as code invariants)

| # | Rule | Enforced in |
|---|------|-------------|
| R1 | Final decision ∈ {CALL, PUT, NO_TRADE} | `decision/` |
| R2 | Confidence < 70% → NO_TRADE | `decision/confidence.py` |
| R3 | Conflicting buy/sell evidence → NO_TRADE | `decision/engine.py` |
| R4 | Only approved non-NO_TRADE signals are delivered | `telegram/dispatcher.py` |
| R5 | No auto broker execution anywhere | global (no such module) |
| R6 | Secrets only in `.env`; never in code/chat/Telegram | `config/` |
| R7 | User sessions fully isolated (no cross-user leakage) | `sessions/`, `users/` |
| R8 | Signal arrives ~15–20s before target candle; stale→reject; dup→block | `timing/` |
| R9 | Fail-safe NO_TRADE when required data unavailable | `filters/`, `analysis/` |
| R10 | Learning may never bypass safety gates | `learning/` |

---

## 2. Tech Stack (chosen for this environment)

| Concern | Choice | Why |
|---------|--------|-----|
| Language | Python 3.11 (async) | present in env |
| Telegram | `python-telegram-bot` v21+ (async, httpx-based) | button/callback-first UX, proxy support |
| HTTP | `httpx` (async) | market + news + Telegram transport |
| Config | `pydantic-settings` + `.env` | typed, safe, secret separation |
| Storage | SQLite via `aiosqlite` | zero-infra, persistent state, single process |
| Scheduling | `asyncio` tasks + internal timing engine (APScheduler optional later) | precise candle timing |
| Logging | stdlib `logging` + `RotatingFileHandler` | 24/7 ops |
| Testing | `pytest` + `pytest-asyncio` | per-module testability (doc §28) |

**Transport note:** this sandbox cannot reach `api.telegram.org` directly
(confirmed). Every network call goes through one `HttpClient` that supports a
`TELEGRAM_PROXY` / `MARKET_PROXY` env var, plus a **Mock transport** so the
entire bot is testable offline. Live Telegram delivery happens on the user's
network / VPS.

---

## 3. Repository Layout

```
kkproject69/
├── PLAN.md
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── pytest.ini
├── main.py                     # entrypoint (bot + scheduler + watchdog)
├── hacker/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py         # pydantic Settings from .env
│   ├── models/
│   │   ├── __init__.py
│   │   ├── candle.py           # normalized Candle
│   │   ├── signal.py           # FinalSignal / Decision / enums
│   │   ├── outcome.py          # Outcome, ResultType, MTG
│   │   └── enums.py            # Direction, Timeframe, AccessLevel, ...
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── db.py               # SQLite pool + schema migration
│   │   └── repositories/       # users, sessions, signals, outcomes, stats
│   ├── net/
│   │   ├── __init__.py
│   │   ├── http.py             # shared async client + proxy + retry
│   │   └── mock_transport.py   # offline dev/test transport
│   ├── data_sources/
│   │   ├── __init__.py
│   │   ├── base.py             # MarketDataSource ABC
│   │   ├── novex.py            # NovexAI adapter (tested source)
│   │   ├── oanda.py            # optional live source (stub)
│   │   └── cortex.py           # Cortex/Quotex candle adapter (stub)
│   ├── calendar/
│   │   ├── __init__.py
│   │   └── forex_factory.py    # weekly JSON → normalized events
│   ├── analysis/
│   │   ├── __init__.py
│   │   └── market_analyzer.py  # trend, S/R, structure, momentum, FVG, ...
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── base.py             # Strategy ABC: direction, confidence, reason, risk, invalidation
│   │   ├── registry.py         # authoritative 11-strategy registry
│   │   ├── aggregator.py       # combine 11 → structured evidence
│   │   └── impl/               # one module per strategy (see §6)
│   ├── decision/
│   │   ├── __init__.py
│   │   ├── confidence.py       # 70% gate
│   │   ├── engine.py           # evidence → CALL/PUT/NO_TRADE
│   │   └── ai.py               # AI service layer (reasoning/approval)
│   ├── filters/
│   │   ├── __init__.py
│   │   ├── market_filters.py   # trend/condition/duplicate/cooldown
│   │   ├── news_filter.py      # high-impact event window
│   │   └── payout_filter.py    # min payout
│   ├── timing/
│   │   ├── __init__.py
│   │   └── engine.py           # candle start calc, lead time, stale/dup
│   ├── sessions/
│   │   ├── __init__.py
│   │   ├── manager.py          # per-user session lifecycle
│   │   ├── manual.py           # Manual live signal service
│   │   ├── combined.py         # all-11 combined session
│   │   ├── single.py           # single-strategy session
│   │   └── otc.py              # OTC future-signal workflow
│   ├── results/
│   │   ├── __init__.py
│   │   ├── evaluator.py        # outcome resolution
│   │   ├── statistics.py       # session/strategy/pair stats
│   │   └── loss_review.py      # AI loss review
│   ├── learning/
│   │   ├── __init__.py
│   │   └── performance.py      # strategy performance + safe adaptation
│   ├── paper/
│   │   └── __init__.py         # paper trading engine
│   ├── users/
│   │   ├── __init__.py
│   │   └── access.py           # FREE/PREMIUM/VIP/ADMIN, server-side gate
│   ├── reporting/
│   │   └── weekly.py           # weekly report generator
│   └── telegram/
│       ├── __init__.py
│       ├── bot.py              # application, handlers, polling
│       ├── ui.py               # button menus / keyboards
│       ├── dispatcher.py       # approved signals → channel
│       ├── sender.py           # branded signal/result/review messages
│       └── channel.py          # channel routing config
└── tests/
    ├── conftest.py
    ├── test_data_sources.py
    ├── test_analysis.py
    ├── test_strategies.py
    ├── test_decision.py
    ├── test_filters.py
    ├── test_timing.py
    ├── test_sessions.py
    ├── test_results.py
    ├── test_paper.py
    └── test_telegram.py
```

---

## 4. Data Model (SQLite)

- **users** — `telegram_id`, `access_level` (FREE/PREMIUM/VIP/ADMIN), `settings_json`
- **sessions** — `id`, `user_id`, `type` (combined/single/otc/paper), `strategy_id`, `pairs`, `status`, `started_at`, `ended_at`
- **signals** — `id`, `session_id`, `user_id`, `pair`, `direction`, `timeframe`, `entry_time`, `target_candle`, `payout`, `confidence`, `strategy/evidence`, `reason`, `ai_verdict`, `generated_at`, `delivered_at`, `status`
- **outcomes** — `id`, `signal_id`, `result` (DIRECT_WIN/MTG_WIN/BREAK_EVEN/LOSS), `mtg_count`, `review_json`
- **strategy_stats** — per-strategy + per-pair + per-session win/loss/accuracy counters
- **paper_trades** — virtual stake, entries, MTG path, results, drawdown
- **events** (cache) — Forex Factory events for the news filter window

All timestamps stored UTC; source timezone handled in the adapter layer.

---

## 5. Core Flow (code path)

```
[MarketDataSource] → normalize → [Candle list]
        ↘
[ForexFactory calendar] → normalized events → [NewsFilter]
        ↘
[MarketAnalyzer] → structured evidence (trend, S/R, momentum, FVG, structure…)
        ↘
[StrategyRegistry] → 11 × StrategyResult(direction, confidence, reason, risk, invalidation)
        ↘
[Aggregator] → combined evidence (agreement / conflict / strength)
        ↘
[ConfidenceEngine] → ≥70% gate
        ↘
[DecisionEngine + AI layer] → CALL / PUT / NO_TRADE + reasoning
        ↘
[Filters: news, payout, cooldown, duplicate, stale] → pass / block
        ↘
[SignalTimingEngine] → schedule for target candle − lead time
        ↘
[TelegramDispatcher → TelegramSignalSender] → branded message → private channel
        ↘
[ResultEvaluator] → outcome → [LossReview / Learning / Stats]
```

---

## 6. The 11-Strategy Engine (⚠️ open item)

The three source documents **explicitly state the exact names & rule sets of the
11 strategies were not retrievable** and must come from the user's original
authoritative spec — they must **not be invented**.

The docs retain these **concepts** as placeholders: Support & Resistance,
Trendline, Fair Value Gap (FVG), Breakout, Fakeout, IFEG, Volume Imbalance,
Market Structure, MTG methodology, Money Management, Risk Control.

**Plan:** implement a `StrategyRegistry` where each strategy is a class exposing
`direction`, `confidence`, `reason`, `risk`, `invalidation`. I will scaffold all
11 as concrete modules **using the retained concept names**, with each one's
rule set clearly marked `# TODO: confirm against original 11-strategy spec`.
The moment the original spec is provided, each module's entry/confirmation/
invalidation rules are updated in place (registry & aggregator need no rewrite).

---

## 7. Telegram UX (button-first)

Main menu → submenus, all via `InlineKeyboardMarkup` callbacks (no slash-command
memorization):

- 🚀 LIVE SESSION → 🧩 COMBINED / 🎯 SINGLE STRATEGY → pick strategy → pick pairs → start
- 📡 LIVE SIGNAL (manual: strategy + pair → analyze → CALL/PUT/NO_TRADE)
- 🔮 OTC FUTURE SIGNAL
- 📈 MARKET ANALYSIS · 📰 NEWS SIGNAL · 🧠 AI ANALYSIS
- 🛡️ MARKET FILTERS · 💰 PAYOUT FILTER
- 📊 SESSION RESULT (partial/current on demand)
- 🧪 PAPER TRADING · 📚 AI TRADING COURSE
- 👑 VIP ZONE · 💎 PREMIUM · ⚙️ SETTINGS · 👤 MY ACCOUNT · ℹ️ HELP/ABOUT

Admin controls kept in a separate admin-only menu. Signal messages use the
branded HACKER GenAI+ format (pair, direction, timeframe, entry/next-candle,
payout, confidence, risk, strategy/evidence, why, AI verdict, risk warning).

---

## 8. Build Order (incremental, each phase ends testable)

| Phase | Deliverable | Exit criteria |
|-------|-------------|---------------|
| **P0** | Repo scaffold, `.env.example`, `config`, models/enums, SQLite schema, logging | imports clean, settings load, DB migrates |
| **P1** | `net.http` (proxy+retry+mock), MarketDataSource ABC, NovexAI adapter, Candle normalization, ForexFactory adapter | mock & real fetch tests pass |
| **P2** | `MarketAnalyzer` (trend/S-R/momentum/FVG/structure) + filters (news/payout/cooldown/dup) | unit tests on canned candles |
| **P3** | Strategy base + registry + aggregator + 11 scaffolded strategies | each strategy testable independently |
| **P4** | Confidence engine, decision engine, AI service layer (mock first) | CALL/PUT/NO_TRADE + <70% + conflict tests |
| **P5** | Signal timing engine (candle start, lead time, stale/dup protection) | 15–20s timing tests, tz tests |
| **P6** | Telegram bot: menus, handlers, dispatcher, branded sender, channel routing | offline bot tests pass; live smoke on user network |
| **P7** | Sessions: manual, combined, single-strategy, OTC future-signal | session lifecycle + isolation tests |
| **P8** | Results: evaluator, statistics, AI loss review, learning/performance | outcome + review tests |
| **P9** | Paper trading, weekly reports, premium/VIP/access, admin menu | paper + report + access tests |
| **P10** | Watchdog/restart, health checks, logging/monitoring, full E2E test suite, README | full suite green, 24/7-ready |

---

## 9. Environment Variables (`.env`)

```
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHANNEL_ID=
TELEGRAM_PROXY=          # optional (Telegram-only route)
MARKET_PROXY=            # optional (market-data route, independent)
MARKET_SOURCE=novex      # novex | oanda | cortex | mock
NOVEX_BASE_URL=
NOVEX_API_KEY=
FOREX_FACTORY_URL=https://nvv.fra1.cdn.digitaloceanspaces.com/...  # weekly JSON
AI_API_URL=              # reasoning/approval service (mock default)
AI_API_KEY=
MIN_CONFIDENCE=70
MIN_PAYOUT=0
SIGNAL_LEAD_SECONDS=17   # 15–20s before candle
DB_PATH=data/hacker.db
LOG_LEVEL=INFO
```

Secrets never committed; `.env.example` ships with placeholders only.

---

## 10. Testing Strategy (maps to doc §28)

01 adapters · 02 normalization/bad payloads · 03 each strategy · 04 combined ·
05 single · 06 manual · 07 CALL/PUT/NO_TRADE · 08 <70% · 09 conflicting ·
10 news/payout filters · 11 duplicate protection · 12 15–20s timing ·
13 channel delivery (mock transport) · 14 partial/session reports ·
15 AI loss review · 16 user isolation · 17 paper trading · 18 restart/recovery ·
19 24/7 ops. CI-style: `pytest -q` must pass before each phase is considered done.

---

## 11. Open Questions (blocking inputs needed from you)

1. **The 11 strategies** — do you have the original spec (exact names + entry/
   confirmation/invalidation rules)? Or should I scaffold with the 11 concept
   names retained in the docs and refine later?
2. **Telegram credentials** — will you drop a bot token + channel ID into `.env`
   now, or should I build fully with placeholders + a mock transport first?
3. **Market data** — is there a concrete NovexAI base URL / key (or another
   source) to wire, or should the adapter start against the mock/recorded data?
4. **First milestone scope** — full skeleton across all modules (P0–P10), or a
   vertical slice first (market→analysis→strategy→signal→Telegram), then expand?
