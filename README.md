# HACKER GenAI+

An AI **Trading Assistant** and signal/analysis platform delivered as a premium
Telegram bot. It consumes market candles + economic-news context, runs market
analysis, evaluates an 11-strategy engine, applies an AI decision layer with
confidence/risk/payout/news filters, and delivers branded **CALL / PUT /
NO_TRADE** signals to a private Telegram channel — with 15–20s pre-candle
timing, outcome tracking, AI loss reviews and learning.

> **Important:** automatic broker execution / real-money order placement is
> **out of scope**. This is a signal & analysis platform only.

See **[PLAN.md](PLAN.md)** for the full architecture and build plan.

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env -> set TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, MARKET_SOURCE, etc.

python main.py
```

Run the test suite:

```bash
pytest -q
```

## Package layout

```
hacker/
├── config/        # settings (.env)
├── models/        # Candle, Signal, Decision, Outcome, enums
├── storage/       # SQLite + repositories
├── net/           # shared HTTP client (proxy + retry)
├── data_sources/  # market adapters (novex / mock / oanda / cortex)
├── calendar/      # Forex Factory news adapter
├── analysis/      # MarketAnalyzer
├── strategies/    # 11-strategy engine + aggregator
├── decision/      # confidence gate + AI decision layer
├── filters/       # news / payout / market filters
├── timing/        # candle-entry timing engine
├── sessions/      # manual / combined / single / OTC sessions
├── results/       # outcome evaluation + stats + loss review
├── learning/      # strategy performance + safe adaptation
├── paper/         # paper trading
├── users/         # FREE/PREMIUM/VIP/ADMIN access
├── reporting/     # weekly reports
└── telegram/      # bot, menus, dispatcher, branded sender
```
