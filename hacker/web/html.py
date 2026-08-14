"""Black & white HTML templates for the dashboard and admin panel.

Deliberately monochrome: white page, black type, black borders, grey for
muted text. No JavaScript frameworks, no external assets — everything is
inline so the panel works with zero network dependency and zero build step.
"""
from __future__ import annotations

import html as _html
from typing import Any


def esc(value: Any) -> str:
    return _html.escape(str(value if value is not None else ""))


_CSS = """
:root{
  --ink:#000; --paper:#fff; --line:#000; --mut:#555; --faint:#999;
  --ghost:#eee; --code:'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{background:var(--paper);color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
  font-size:15px;line-height:1.5;-webkit-font-smoothing:antialiased}
a{color:var(--ink);text-decoration:none}
a:hover{text-decoration:underline}
.wrap{max-width:1080px;margin:0 auto;padding:0 20px}
header.top{background:var(--ink);color:var(--paper);border-bottom:3px solid var(--ink)}
header.top .wrap{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;padding-top:14px;padding-bottom:14px}
.brand{font-family:var(--code);font-size:20px;font-weight:700;letter-spacing:2px}
.brand span{color:#fff;opacity:.55}
nav{display:flex;gap:18px;font-family:var(--code);font-size:13px;letter-spacing:1px}
nav a{color:var(--paper);opacity:.75;text-decoration:none;padding:6px 10px;border:1px solid transparent}
nav a:hover{opacity:1}
nav a.on{border-color:var(--paper)}
main{min-height:70vh;padding:26px 0 40px}
footer{border-top:1px solid var(--line);padding:18px 0 40px;color:var(--mut);
  font-family:var(--code);font-size:12px;text-align:center}
h1{font-family:var(--code);font-size:24px;letter-spacing:1px;margin:0 0 4px}
h2{font-family:var(--code);font-size:16px;letter-spacing:1px;margin:26px 0 10px;text-transform:uppercase}
h3{font-family:var(--code);font-size:13px;margin:0 0 8px;text-transform:uppercase;letter-spacing:1px}
.sub{color:var(--mut);font-size:13px;margin:0 0 18px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin:16px 0}
.card{border:2px solid var(--line);padding:14px 16px;background:var(--paper)}
.card .k{font-family:var(--code);font-size:11px;letter-spacing:1px;color:var(--mut);text-transform:uppercase}
.card .v{font-family:var(--code);font-size:22px;font-weight:700;margin-top:2px;word-break:break-word}
.card .v small{font-size:13px;font-weight:400;color:var(--mut)}
table{width:100%;border-collapse:collapse;margin:8px 0 20px;font-family:var(--code);font-size:13px}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{border-top:2px solid var(--line);border-bottom:2px solid var(--line);text-transform:uppercase;font-size:11px;letter-spacing:1px}
tbody tr:nth-child(even){background:var(--ghost)}
.badge{display:inline-block;border:1px solid var(--line);padding:1px 8px;font-size:11px;
  font-family:var(--code);letter-spacing:1px;text-transform:uppercase}
.badge.fill{background:var(--ink);color:var(--paper);border-color:var(--ink)}
.badge.mut{color:var(--mut)}
button,.btn{font-family:var(--code);font-size:13px;letter-spacing:1px;cursor:pointer;
  background:var(--ink);color:var(--paper);border:2px solid var(--ink);padding:8px 14px;text-transform:uppercase}
button:hover,.btn:hover{background:var(--paper);color:var(--ink)}
button.ghost,.btn.ghost{background:var(--paper);color:var(--ink)}
button.ghost:hover{background:var(--ink);color:var(--paper)}
button:disabled{opacity:.4;cursor:not-allowed}
input,select,textarea{font-family:var(--code);font-size:13px;color:var(--ink);
  background:var(--paper);border:1.5px solid var(--line);padding:8px 10px;width:100%;border-radius:0}
input:focus,select:focus,textarea:focus{outline:none;box-shadow:0 0 0 2px var(--ink)}
label{font-family:var(--code);font-size:11px;letter-spacing:1px;text-transform:uppercase;color:var(--mut)}
.field{margin:10px 0}
.row{display:flex;gap:10px;flex-wrap:wrap;align-items:flex-end}
.row .field{flex:1;min-width:180px}
.form-card{border:2px solid var(--line);padding:18px;max-width:640px;margin:14px 0}
.banner{border:2px solid var(--line);padding:12px 14px;margin:12px 0;font-family:var(--code);font-size:13px}
.banner.ok{background:var(--ink);color:var(--paper)}
.tabs{display:flex;gap:0;flex-wrap:wrap;border-bottom:2px solid var(--line);margin:18px 0 0}
.tab{font-family:var(--code);font-size:12px;letter-spacing:1px;padding:9px 14px;cursor:pointer;
  border:2px solid var(--line);border-bottom:none;margin-right:-2px;background:var(--paper);text-transform:uppercase}
.tab.on{background:var(--ink);color:var(--paper)}
.pane{display:none;padding:16px 0}
.pane.on{display:block}
.logbox{font-family:var(--code);font-size:12px;background:#fff;border:2px solid var(--line);
  padding:12px;height:340px;overflow:auto;white-space:pre-wrap;word-break:break-word;color:#000}
.mono{font-family:var(--code)}
.mut{color:var(--mut)}
.small{font-size:12px}
.right{text-align:right}
.center{text-align:center}
.mt{margin-top:14px}
.note{color:var(--mut);font-size:12px;font-family:var(--code)}
"""

_LAYOUT = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<title>__TITLE__</title>
<style>__CSS__</style>
</head>
<body>
<header class="top"><div class="wrap">
  <div class="brand">HACKER <span>GenAI+</span></div>
  <nav>
    <a href="/" class="__HOME__">HOME</a>
    <a href="/signals" class="__SIGNALS__">SIGNALS</a>
    <a href="/admin" class="__ADMIN__">ADMIN</a>
  </nav>
</div></header>
<main><div class="wrap">
__CONTENT__
</div></main>
<footer>HACKER GenAI+ &mdash; AI trading assistant. Signals are analysis only, not financial advice.</footer>
</body>
</html>
"""


def render(title: str, content: str, active: str = "") -> str:
    nav = {
        "home": "HOME",
        "signals": "SIGNALS",
        "admin": "ADMIN",
    }
    cls = {k: ("on" if k == active else "") for k in nav}
    out = _LAYOUT.replace("__CSS__", _CSS)
    out = out.replace("__TITLE__", esc(title))
    out = out.replace("__CONTENT__", content)
    out = out.replace("__HOME__", cls["home"])
    out = out.replace("__SIGNALS__", cls["signals"])
    out = out.replace("__ADMIN__", cls["admin"])
    return out


def _badge(text: str, fill: bool = False) -> str:
    return f'<span class="badge {"fill" if fill else ""}">{esc(text)}</span>'


def _signal_rows(signals: list[dict[str, Any]]) -> str:
    if not signals:
        return '<p class="sub">No signals yet. They appear here as soon as the engine produces one.</p>'
    rows = []
    for s in signals:
        direction = str(s.get("direction") or "NO_TRADE")
        confidence = s.get("confidence")
        conf_text = f"{float(confidence):.0f}%" if confidence else "—"
        payout = s.get("payout")
        payout_text = str(payout) if payout is not None else "N/A"
        status = str(s.get("status") or "PENDING")
        rows.append(
            "<tr>"
            f"<td class='mono'>{esc((s.get('generated_at') or '')[:19].replace('T',' '))}</td>"
            f"<td><b>{esc(s.get('pair'))}</b></td>"
            f"<td>{_badge(direction, fill=direction in ('CALL','PUT'))}</td>"
            f"<td>{esc(s.get('timeframe') or '')}</td>"
            f"<td>{esc(conf_text)}</td>"
            f"<td>{esc(payout_text)}</td>"
            f"<td>{_badge(status, fill=status=='DELIVERED')}</td>"
            "</tr>"
        )
    return "".join(rows)


def _signal_table(signals: list[dict[str, Any]]) -> str:
    return (
        "<table><thead><tr>"
        "<th>Time (UTC)</th><th>Pair</th><th>Action</th><th>TF</th>"
        "<th>Conf</th><th>Payout</th><th>Status</th>"
        "</tr></thead><tbody>"
        + _signal_rows(signals)
        + "</tbody></table>"
    )


def home(status: dict[str, Any], signals: list[dict[str, Any]]) -> str:
    online = bool(status.get("running"))
    enabled = bool(status.get("signals_enabled"))
    stats = status.get("stats") or {}
    deploy = status.get("deploy") or {}
    uptime = int(status.get("uptime_seconds") or 0)
    uh, um = divmod(uptime // 60, 60)
    ud, uh = divmod(uh, 24)

    content = (
        "<h1>HACKER GenAI+</h1>"
        f"<p class='sub'>AI trading assistant &mdash; v{esc(status.get('version'))} &middot; "
        f"Python {esc(status.get('python'))} &middot; {esc((deploy.get('platform') or 'local').upper())}</p>"
        '<div class="grid">'
        f"<div class='card'><div class='k'>Bot Status</div><div class='v'>"
        f"{_badge('ONLINE' if online else 'STANDBY', fill=online)}</div></div>"
        f"<div class='card'><div class='k'>Signal Gate</div><div class='v'>"
        f"{_badge('ON' if enabled else 'OFF', fill=enabled)}</div></div>"
        f"<div class='card'><div class='k'>Uptime</div><div class='v'>{ud}d {uh}h {um}m</div></div>"
        f"<div class='card'><div class='k'>Signals</div><div class='v'>"
        f"{esc(status.get('signals_total'))} <small>/ {esc(status.get('signals_delivered'))} delivered</small></div></div>"
        f"<div class='card'><div class='k'>Win Rate</div><div class='v'>{esc(stats.get('accuracy'))}%</div></div>"
        f"<div class='card'><div class='k'>Users</div><div class='v'>{esc(status.get('users_total'))}</div></div>"
        "</div>"
        "<h2>Latest Signals</h2>"
        + _signal_table(signals)
        + "<p class='note'>Auto-refresh enabled &mdash; this page polls live status every 15s.</p>"
        "<script>setTimeout(function(){location.reload();},15000);</script>"
    )
    return render("HACKER GenAI+ — Dashboard", content, "home")


def signals_page(signals: list[dict[str, Any]]) -> str:
    content = (
        "<h1>Signal Feed</h1>"
        "<p class='sub'>Every approved signal produced by the engine, newest first.</p>"
        + _signal_table(signals)
    )
    return render("HACKER GenAI+ — Signals", content, "signals")


def login_page(msg: str = "", enabled: bool = True) -> str:
    if not enabled:
        content = (
            "<h1>Admin Access Disabled</h1>"
            "<p class='sub'>Set <code>WEB_ADMIN_PASSWORD</code> in your environment "
            "(Railway variables / .env) to enable the control panel.</p>"
        )
    else:
        banner = f'<div class="banner ok">{esc(msg)}</div>' if msg else ""
        content = (
            "<h1>Admin Login</h1>"
            f"{banner}"
            '<div class="form-card">'
            "<form method='post' action='/login'>"
            "<div class='field'><label>Username</label>"
            "<input name='username' autocomplete='username' required></div>"
            "<div class='field'><label>Password</label>"
            "<input name='password' type='password' autocomplete='current-password' required></div>"
            "<div class='mt'><button type='submit'>Sign In</button></div>"
            "</form></div>"
        )
    return render("HACKER GenAI+ — Admin", content, "admin")


def _user_rows(users: list[dict[str, Any]]) -> str:
    if not users:
        return '<p class="sub">No users yet — they register when they message the bot.</p>'
    rows = []
    for u in users:
        banned = bool(u.get("banned"))
        level = str(u.get("access_level") or "FREE")
        rows.append(
            "<tr>"
            f"<td><code>{esc(u.get('telegram_id'))}</code></td>"
            f"<td>{esc(u.get('username') or '—')}</td>"
            f"<td>{_badge(level, fill=level=='ADMIN')}</td>"
            f"<td>{_badge('BANNED' if banned else 'ACTIVE', fill=banned)}</td>"
            f"<td class='small mut'>{esc((u.get('created_at') or '')[:19].replace('T',' '))}</td>"
            "<td class='right'>"
            "<form method='post' action='/api/admin/users' style='display:inline'>"
            f"<input type='hidden' name='telegram_id' value='{esc(u.get('telegram_id'))}'>"
            "<select name='level' style='width:auto;display:inline-block;min-width:110px'>"
            + "".join(
                f"<option value='{lv}' {'selected' if lv == level else ''}>{lv}</option>"
                for lv in ("FREE", "PREMIUM", "VIP", "ADMIN")
            )
            + "</select> "
            "<select name='banned' style='width:auto;display:inline-block;min-width:100px'>"
            f"<option value='0' {'selected' if not banned else ''}>ACTIVE</option>"
            f"<option value='1' {'selected' if banned else ''}>BANNED</option>"
            "</select> "
            "<button type='submit' class='ghost'>SAVE</button>"
            "</form></td>"
            "</tr>"
        )
    return "".join(rows)


def _settings_form(settings: dict[str, Any]) -> str:
    market = str(settings.get("market_source") or "auto")
    signals_on = bool(settings.get("signals_enabled"))
    confluence = bool(settings.get("require_confluence"))
    volatile = bool(settings.get("avoid_volatile"))

    def sel(name: str, options: list[str], current: str) -> str:
        opts = "".join(
            f"<option value='{o}' {'selected' if o == current else ''}>{o}</option>"
            for o in options
        )
        return f"<select name='{name}'>{opts}</select>"

    return (
        "<form method='post' action='/api/admin/settings'>"
        "<div class='row'>"
        f"<div class='field'><label>Min Confidence (%)</label>"
        f"<input name='min_confidence' type='number' step='1' min='0' max='100' value='{esc(settings.get('min_confidence', 70))}'></div>"
        f"<div class='field'><label>Min Payout (%)</label>"
        f"<input name='min_payout' type='number' step='1' min='0' value='{esc(settings.get('min_payout', 0))}'></div>"
        f"<div class='field'><label>Signal Lead (seconds)</label>"
        f"<input name='signal_lead_seconds' type='number' step='1' min='0' max='120' value='{esc(settings.get('signal_lead_seconds', 17))}'></div>"
        f"<div class='field'><label>Cooldown (seconds)</label>"
        f"<input name='cooldown_seconds' type='number' step='1' min='0' value='{esc(settings.get('cooldown_seconds', 60))}'></div>"
        "</div><div class='row'>"
        f"<div class='field'><label>Market Source</label>{sel('market_source', ['auto', 'mock'], market)}</div>"
        f"<div class='field'><label>Require Confluence</label>{sel('require_confluence', ['off', 'on'], 'on' if confluence else 'off')}</div>"
        f"<div class='field'><label>Avoid Volatile</label>{sel('avoid_volatile', ['off', 'on'], 'on' if volatile else 'off')}</div>"
        f"<div class='field'><label>Signal Delivery</label>{sel('signals_enabled', ['on', 'off'], 'on' if signals_on else 'off')}</div>"
        "</div>"
        "<div class='mt'><button type='submit'>SAVE SETTINGS</button></div>"
        "</form>"
    )


def _audit_rows(audit: list[dict[str, Any]]) -> str:
    if not audit:
        return '<p class="sub">No admin actions recorded yet.</p>'
    rows = []
    for a in audit:
        rows.append(
            "<tr>"
            f"<td class='small'>{esc((a.get('created_at') or '')[:19].replace('T',' '))}</td>"
            f"<td><b>{esc(a.get('actor'))}</b></td>"
            f"<td>{esc(a.get('action'))}</td>"
            f"<td class='small mut'>{esc(a.get('detail') or '')}</td>"
            "</tr>"
        )
    return "".join(rows)


_ADMIN_JS = """
<script>
function tab(name){
  document.querySelectorAll('.tab').forEach(function(t){t.classList.toggle('on', t.dataset.tab===name)});
  document.querySelectorAll('.pane').forEach(function(p){p.classList.toggle('on', p.dataset.pane===name)});
  if(name==='logs'){pullLogs();}
}
function pullLogs(){
  fetch('/api/admin/logs').then(function(r){return r.json()}).then(function(d){
    var box=document.getElementById('logbox');
    if(box){box.textContent=(d.logs||[]).join('\\n');}
  }).catch(function(){});
}
setInterval(function(){if(document.querySelector('.pane.on')&&document.querySelector('.pane.on').dataset.pane==='logs'){pullLogs();}},3000);
setInterval(function(){
  fetch('/api/status').then(function(r){return r.json()}).then(function(d){
    var el=document.getElementById('live-status');
    if(el){el.textContent=((d.running?'ONLINE':'STANDBY')+' | SIGNALS '+(d.signals_enabled?'ON':'OFF')+' | UP '+Math.floor(d.uptime_seconds)+'s | '+d.signals_total+' signals');}
  }).catch(function(){});
},5000);
</script>
"""


def admin_page(
    status: dict[str, Any],
    users: list[dict[str, Any]],
    signals: list[dict[str, Any]],
    settings: dict[str, Any],
    audit: list[dict[str, Any]],
    msg: str = "",
) -> str:
    banner = f'<div class="banner ok">{esc(msg)}</div>' if msg else ""
    online = bool(status.get("running"))
    enabled = bool(status.get("signals_enabled"))
    stats = status.get("stats") or {}
    pairs = [
        "USDBDT-OTC", "USDPKR-OTC", "BTCUSD-OTC", "EURUSD-OTC", "GBPUSD-OTC",
        "USDJPY-OTC", "AUDUSD-OTC", "USDCAD-OTC", "EURGBP-OTC", "USDCHF-OTC",
    ]
    pair_opts = "".join(f"<option value='{p}'>{p}</option>" for p in pairs)
    tf_opts = "".join(
        f"<option value='{t}'>{t}</option>" for t in ("1m", "5m", "15m", "30m", "1h")
    )

    content = (
        "<h1>Control Panel</h1>"
        "<p class='sub'><span id='live-status' class='mono'></span></p>"
        f"{banner}"
        '<div class="grid">'
        f"<div class='card'><div class='k'>Bot</div><div class='v'>{_badge('ONLINE' if online else 'STANDBY', fill=online)}</div></div>"
        f"<div class='card'><div class='k'>Signal Gate</div><div class='v'>{_badge('ON' if enabled else 'OFF', fill=enabled)}</div></div>"
        f"<div class='card'><div class='k'>Signals</div><div class='v'>{esc(status.get('signals_total'))}</div></div>"
        f"<div class='card'><div class='k'>Win Rate</div><div class='v'>{esc(stats.get('accuracy'))}%</div></div>"
        f"<div class='card'><div class='k'>Users</div><div class='v'>{esc(status.get('users_total'))}</div></div>"
        f"<div class='card'><div class='k'>Market</div><div class='v'>{esc(status.get('market_source'))}</div></div>"
        "</div>"

        '<div class="tabs">'
        '<div class="tab on" data-tab="overview" onclick="tab(\'overview\')">Overview</div>'
        '<div class="tab" data-tab="bot" onclick="tab(\'bot\')">Bot</div>'
        '<div class="tab" data-tab="users" onclick="tab(\'users\')">Users</div>'
        '<div class="tab" data-tab="settings" onclick="tab(\'settings\')">Settings</div>'
        '<div class="tab" data-tab="signals" onclick="tab(\'signals\')">Signals</div>'
        '<div class="tab" data-tab="logs" onclick="tab(\'logs\')">Logs</div>'
        '<div class="tab" data-tab="audit" onclick="tab(\'audit\')">Audit</div>'
        "</div>"

        # ---- overview
        '<div class="pane on" data-pane="overview">'
        "<div class='row'>"
        f"<form method='post' action='/api/admin/bot'><input type='hidden' name='action' value='{'stop' if online else 'start'}'>"
        f"<button type='submit'>{'STOP BOT' if online else 'START BOT'}</button></form>"
        f"<form method='post' action='/api/admin/signals'><input type='hidden' name='enabled' value='{'off' if enabled else 'on'}'>"
        f"<button type='submit' class='ghost'>{'DISABLE SIGNALS' if enabled else 'ENABLE SIGNALS'}</button></form>"
        f"<form method='post' action='/api/admin/ping'><button type='submit' class='ghost'>SEND DEPLOY PING</button></form>"
        f"<form method='post' action='/logout'><button type='submit' class='ghost'>LOGOUT</button></form>"
        "</div>"
        "<h2>Test Signal</h2>"
        '<div class="form-card">'
        "<form method='post' action='/api/admin/generate'><div class='row'>"
        f"<div class='field'><label>Pair</label><select name='pair'>{pair_opts}</select></div>"
        f"<div class='field'><label>Timeframe</label><select name='timeframe'>{tf_opts}</select></div>"
        "</div><div class='mt'><button type='submit'>GENERATE &amp; SEND SIGNAL</button></div></form>"
        "</div>"
        "<h2>Broadcast to Channel</h2>"
        '<div class="form-card">'
        "<form method='post' action='/api/admin/broadcast'>"
        "<div class='field'><label>Message (HTML allowed)</label>"
        "<textarea name='text' rows='3' placeholder='Type an announcement for the Telegram channel…'></textarea></div>"
        "<div class='mt'><button type='submit'>BROADCAST</button></div></form>"
        "</div></div>"

        # ---- bot
        '<div class="pane" data-pane="bot">'
        "<p class='sub'>Lifecycle controls for the Telegram poller and signal delivery.</p>"
        "<div class='row'>"
        f"<form method='post' action='/api/admin/bot'><input type='hidden' name='action' value='start'>"
        f"<button type='submit'>START BOT</button></form>"
        f"<form method='post' action='/api/admin/bot'><input type='hidden' name='action' value='stop'>"
        f"<button type='submit' class='ghost'>STOP BOT</button></form>"
        f"<form method='post' action='/api/admin/bot'><input type='hidden' name='action' value='restart'>"
        f"<button type='submit' class='ghost'>RESTART BOT</button></form>"
        f"<form method='post' action='/api/admin/signals'><input type='hidden' name='enabled' value='{'off' if enabled else 'on'}'>"
        f"<button type='submit' class='ghost'>{'DISABLE SIGNALS' if enabled else 'ENABLE SIGNALS'}</button></form>"
        f"<form method='post' action='/api/admin/ping'><button type='submit' class='ghost'>DEPLOY PING</button></form>"
        "</div>"
        "<h2>Runtime Info</h2>"
        "<table><tbody>"
        f"<tr><th>Version</th><td>v{esc(status.get('version'))}</td></tr>"
        f"<tr><th>Python</th><td>{esc(status.get('python'))}</td></tr>"
        f"<tr><th>Telegram</th><td>{_badge('CONFIGURED' if status.get('telegram_configured') else 'NOT CONFIGURED', fill=bool(status.get('telegram_configured')))}</td></tr>"
        f"<tr><th>Started</th><td>{esc(status.get('started_at') or '—')}</td></tr>"
        f"<tr><th>AI Provider</th><td>{esc(status.get('ai_provider'))}</td></tr>"
        f"<tr><th>Platform</th><td>{esc((status.get('deploy') or {}).get('platform'))}</td></tr>"
        f"<tr><th>Environment</th><td>{esc((status.get('deploy') or {}).get('environment'))}</td></tr>"
        f"<tr><th>Service</th><td>{esc((status.get('deploy') or {}).get('service'))}</td></tr>"
        f"<tr><th>Commit</th><td>{esc((status.get('deploy') or {}).get('git_commit') or '—')}</td></tr>"
        "</tbody></table></div>"

        # ---- users
        '<div class="pane" data-pane="users">'
        "<p class='sub'>Access control — set each user's level (FREE / PREMIUM / VIP / ADMIN) or ban them.</p>"
        "<table><thead><tr><th>ID</th><th>Username</th><th>Level</th><th>Status</th><th>Joined</th><th class='right'>Edit</th></tr></thead><tbody>"
        + _user_rows(users)
        + "</tbody></table></div>"

        # ---- settings
        '<div class="pane" data-pane="settings">'
        "<p class='sub'>Runtime overrides applied instantly and persisted across restarts.</p>"
        '<div class="form-card">' + _settings_form(settings) + "</div></div>"

        # ---- signals
        '<div class="pane" data-pane="signals">' + _signal_table(signals) + "</div>"

        # ---- logs
        '<div class="pane" data-pane="logs">'
        "<p class='sub'>Live tail (refreshes every 3s).</p>"
        '<div class="logbox" id="logbox">Loading…</div></div>'

        # ---- audit
        '<div class="pane" data-pane="audit">'
        "<table><thead><tr><th>Time</th><th>Actor</th><th>Action</th><th>Detail</th></tr></thead><tbody>"
        + _audit_rows(audit)
        + "</tbody></table></div>"

        + _ADMIN_JS
    )
    return render("HACKER GenAI+ — Control Panel", content, "admin")
