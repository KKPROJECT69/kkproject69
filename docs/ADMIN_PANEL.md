# Advanced Admin Panel Guide

The admin panel is available at `/admin`. It controls the live Telegram poller,
automatic market scanner, signal safety gate, runtime strategy settings, users,
and operational telemetry.

## Sign in

- URL: `https://YOUR-DOMAIN/admin`
- Default admin ID: `admin`
- Default development password: `$`

Set `WEB_ADMIN_USERNAME` and `WEB_ADMIN_PASSWORD` in Railway (or `.env`) before
putting the service on a public URL. Environment values override the development
defaults. The login cookie is HttpOnly and SameSite=Lax, and expires after
`WEB_SESSION_TTL_HOURS`.

## Start the signal engine

1. Open **Admin → Settings**.
2. Set **Engine Pairs**, **Timeframe**, and **Scan Interval**. Save settings.
3. Open **Admin → Engine** and select **START ENGINE**.

START ENGINE performs three actions atomically:

1. enables the signal delivery gate;
2. starts Telegram polling when Telegram is configured; and
3. starts one continuous background scanner.

Repeated clicks do not create duplicate scanners. The engine can also run in
web-only mode; generated signals are then persisted as pending instead of being
sent to Telegram.

**STOP ENGINE** stops automatic scanning but deliberately leaves the signal
gate unchanged. **RESTART ENGINE** reloads the latest persisted engine settings
and starts a clean cycle. Engine state does not auto-start after a deployment;
an admin must explicitly start it.

## Engine telemetry

The Engine tab shows:

- live/stopped state and start time;
- most recent completed cycle;
- cycle, pair-scan, approved-signal, and error counts;
- the latest provider/scan error;
- active pair, timeframe, and interval configuration.

A provider failure is isolated to its pair. It is logged and counted without
terminating the scanner.

## Tabs

| Tab | Purpose |
|---|---|
| Overview | Engine/gate health, test signal, and Telegram broadcast |
| Engine | Start, stop, restart, configuration summary, telemetry |
| Bot | Control Telegram polling independently of the engine |
| Users | Create users, assign FREE/PREMIUM/VIP/ADMIN, ban/unban |
| Settings | Live safety gates, source, engine schedule, and delivery gate |
| Signals | Most recent persisted signals and delivery state |
| Logs | In-memory operational log, refreshed every three seconds |
| Audit | Persistent history of admin actions |

## Safety controls

- **Signal Gate OFF** blocks Telegram delivery and records attempted signals as
  `BLOCKED`.
- **Minimum Confidence** and **Minimum Payout** reject weak setups.
- **Require Confluence** requires higher-timeframe agreement.
- **Avoid Volatile** rejects volatile market regimes.
- **Cooldown** prevents rapid repeated output for the same pair.
- A maximum of 25 comma-separated engine pairs is accepted by the scanner.
- Automatic broker execution is not implemented; this platform produces
  analysis signals only.

## Admin HTTP routes

All mutation routes require a valid admin session cookie and accept form data.
Unauthenticated calls return `401` (page requests redirect to `/login`).

| Method | Route | Fields |
|---|---|---|
| POST | `/api/admin/engine` | `action=start|stop|restart` |
| POST | `/api/admin/bot` | `action=start|stop|restart` |
| POST | `/api/admin/signals` | `enabled=on|off` |
| POST | `/api/admin/settings` | editable runtime/engine settings |
| POST | `/api/admin/generate` | `pair`, `timeframe` |
| POST | `/api/admin/broadcast` | `text` |
| POST | `/api/admin/users` | `telegram_id`, `level`, `banned` |
| GET | `/api/admin/logs` | latest in-memory logs |
| GET | `/api/admin/audit` | persistent admin audit entries |

Public monitoring routes are `GET /healthz`, `GET /api/status`, and
`GET /api/signals?limit=50`. The status response includes an `engine` object
with live telemetry.

## Recommended Railway variables

```dotenv
WEB_ADMIN_USERNAME=your-private-admin-id
WEB_ADMIN_PASSWORD=use-a-long-unique-password
WEB_SESSION_TTL_HOURS=12
ENGINE_PAIRS=EURUSD-OTC,GBPUSD-OTC,USDJPY-OTC
ENGINE_TIMEFRAME=1m
ENGINE_INTERVAL_SECONDS=60
```

Runtime values saved from the panel are stored in SQLite. Attach a Railway
volume and set `DB_PATH=/data/hacker.db` to preserve them across deployments.
