# HACKER GenAI+

An AI **Trading Assistant** and signal/analysis platform delivered as a premium
Telegram bot **plus a full black-and-white web dashboard with an admin control
panel** — production-ready for **Railway** (or any Docker/Nixpacks host).

It consumes market candles + economic-news context → normalizes them → runs
market analysis → evaluates an **11-strategy engine** → applies an **AI decision
layer** with confidence/risk/payout/news filters → delivers branded
**CALL / PUT / NO_TRADE** signals to a private Telegram channel with **15–20s
pre-candle timing** → tracks outcomes → runs AI loss reviews and learning.

On every deploy it posts a **"deployed & online"** notice to your Telegram
channel automatically.

> **Important:** automatic broker execution / real-money order placement is
> **out of scope**. This is a signal & analysis platform only.

---

## 1. What you get

| Component | What it does |
|-----------|--------------|
| **Telegram bot** | Button-first menus, live/combined/single sessions, OTC future signal, market analysis, backtest, payout ranking, paper trading, admin menu. |
| **Web dashboard** | Plain black & white. Live status, signal feed, win rate, uptime. |
| **Advanced admin panel** | Password-protected. **START ENGINE** launches continuous market scans, enables signals, and brings Telegram delivery online. Includes independent bot/engine controls, live engine telemetry, kill switch, test signals, broadcasts, access management, runtime settings, logs, and audit trail. |
| **Deploy notification** | On startup the bot announces deployment to your Telegram channel. |

---

## 2. Quickstart (local)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt   # runtime + test/lint tooling

cp .env.example .env
# edit .env -> set TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, WEB_ADMIN_PASSWORD, ...

python main.py
```

> Production only needs `requirements.txt` (runtime deps). Use
> `requirements-dev.txt` for local development / running the test suite.

The web dashboard is served on `http://localhost:8000` (set `PORT` to change).
The admin panel is at `/admin` (login with `WEB_ADMIN_USERNAME` /
`WEB_ADMIN_PASSWORD`).

Run the test suite and the linter:

```bash
pytest -q
ruff check .
```

---

## 3. Deploy on Railway (recommended)

1. Push this repo to GitHub (see §7).
2. In Railway: **New Project → Deploy from GitHub repo → `KKPROJECT69/kkproject69`**.
3. Railway auto-detects the build (Nixpacks reads `requirements.txt` +
   `nixpacks.toml`; `railway.json` sets the start command & healthcheck).
   Only runtime dependencies (`requirements.txt`) are installed in production —
   test tooling stays in `requirements-dev.txt`.
4. Add the environment variables from `.env.example` under **Variables**
   (at minimum: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHANNEL_ID`,
   `WEB_ADMIN_PASSWORD`, `ADMIN_IDS`).
5. **Persistence (recommended):** attach a volume at `/data` and set
   `DB_PATH=/data/hacker.db` so signals/users/settings survive restarts.
6. Deploy. Railway runs `python main.py`, healthchecks `GET /healthz`, and the
   bot posts **"HACKER GenAI+ DEPLOYED"** to your Telegram channel on boot.

> `PORT` is injected by Railway automatically — do not hardcode it.

### Alternative: Docker

A `Dockerfile` is included. On Railway choose **Builder = Dockerfile**, or run
anywhere: `docker build -t hacker-genai . && docker run --env-file .env -p 8000:8000 hacker-genai`.

---

## 4. Environment variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `TELEGRAM_BOT_TOKEN` | for bot | — | Bot token from @BotFather |
| `TELEGRAM_CHANNEL_ID` | for bot | — | Channel the signals are posted to |
| `TELEGRAM_PROXY` / `MARKET_PROXY` | no | — | Optional independent proxies |
| `MARKET_SOURCE` | no | `auto` | `auto` (router) or `mock` |
| `QUOTEX_BASE_URL` / `QUOTEX_WS_URL` | no | * | OTC candle endpoints |
| `NOVEX_PAYOUT_URL` | no | * | Payout endpoint |
| `OANDA_BASE_URL` / `OANDA_API_KEY` / `OANDA_ACCOUNT_ID` | no | * | Live forex candles |
| `FOREX_FACTORY_URL` | no | — | News calendar (weekly JSON) |
| `AI_PROVIDER` | no | `local` | `local` \| `gemini` \| `groq` |
| `GEMINI_API_KEY` / `GROQ_API_KEY` | no | — | Optional free AI providers |
| `MIN_CONFIDENCE` / `MIN_PAYOUT` / `SIGNAL_LEAD_SECONDS` | no | `70` / `0` / `17` | Signal safety gates |
| `ENGINE_PAIRS` / `ENGINE_TIMEFRAME` / `ENGINE_INTERVAL_SECONDS` | no | 3 OTC pairs / `1m` / `60` | Automatic scanner schedule |
| `DB_PATH` | no | `data/hacker.db` | SQLite location |
| `LOG_LEVEL` | no | `INFO` | Log verbosity |
| `ADMIN_IDS` | no | — | Comma-separated Telegram admin user IDs |
| `PORT` | no | `8000` | Web port (Railway injects this) |
| `WEB_HOST` | no | `0.0.0.0` | Bind address |
| `WEB_ADMIN_USERNAME` | no | `admin` | Admin panel login |
| `WEB_ADMIN_PASSWORD` | **yes** | — | Admin panel password (empty = panel disabled) |
| `WEB_COOKIE_NAME` / `WEB_SESSION_TTL_HOURS` | no | * | Admin session cookie |
| `DEPLOY_NOTIFY` | no | `true` | Post deploy notice to channel |

---

## 5. Access control model

Four levels, enforced **server-side**:

| Level | Telegram features |
|-------|-------------------|
| `FREE` | Manual signal, market analysis, AI analysis, backtest, paper trading, session |
| `PREMIUM` | + OTC Future Signal, premium zone |
| `VIP` | + VIP zone |
| `ADMIN` | + `/admin` menu (status, toggle signals, broadcast, users) |

- Admins are configured via `ADMIN_IDS` and/or granted `ADMIN` level in the
  web panel.
- **Banning** a user (web panel → Users, or Telegram admin) blocks them from
  the bot entirely.
- Manage levels/ban from the web panel (`/admin` → **Users**) or via the
  Telegram `/admin` menu.

---

## 6. Web dashboard & admin panel

- `/` — public dashboard (status, live signal feed, win rate, uptime)
- `/signals` — full signal feed
- `/admin` — control panel (login required)
- `/healthz` — JSON healthcheck (Railway)
- `/api/status`, `/api/signals` — JSON read APIs

The panel lets you **control everything**: **START ENGINE** atomically enables
signals, starts Telegram when configured, and launches continuous pair scans;
start/stop/restart the bot or engine independently; toggle the signal gate
(kill switch); generate a test signal; broadcast; edit safety and engine
settings; manage users; and watch telemetry, logs, and audit history. Runtime
settings persist across restarts. See [`docs/ADMIN_PANEL.md`](docs/ADMIN_PANEL.md)
for credentials, operations, safety behavior, and the admin HTTP route guide.

---

## 7. Package layout

```
hacker/
├── config/        # typed settings (.env / Railway variables)
├── models/        # Candle, Signal, Decision, Outcome, enums
├── storage/       # SQLite + repositories (+ app settings + audit log)
├── net/           # shared HTTP client (proxy + retry)
├── data_sources/  # market adapters (quotex / novex / oanda / cortex / mock)
├── calendar/      # Forex Factory news adapter
├── analysis/      # MarketAnalyzer + confluence + regime
├── strategies/    # 11-strategy engine + aggregator
├── decision/      # confidence gate + AI decision layer
├── filters/       # news / payout / market filters
├── timing/        # candle-entry timing engine
├── sessions/      # manual / combined / single / OTC sessions
├── results/       # outcome evaluation + stats + loss review
├── learning/      # strategy performance + safe adaptation
├── paper/         # paper trading
├── users/         # FREE/PREMIUM/VIP/ADMIN access + bans
├── reporting/     # weekly reports
├── telegram/      # bot, menus, dispatcher, branded sender
├── runtime.py     # BotController (shared state + full admin control)
└── web/           # FastAPI dashboard + admin panel (black & white)
```

Top-level: `main.py` (entrypoint), `railway.json`, `Procfile`,
`nixpacks.toml`, `Dockerfile`, `.env.example`.
