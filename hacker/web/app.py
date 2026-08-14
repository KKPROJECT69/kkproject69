"""FastAPI web app — public dashboard + admin control panel.

All state flows through the :class:`BotController`, so the web layer is a thin,
pure-HTTP front for the same live system the Telegram bot uses.
"""
from __future__ import annotations

from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from .auth import AdminAuth
from .html import (
    admin_page,
    home,
    login_page,
    signals_page,
)

# Settings keys editable from the panel (mapped to BotController.SETTING_SCHEMA).
_EDITABLE_SETTINGS = [
    "min_confidence",
    "min_payout",
    "signal_lead_seconds",
    "cooldown_seconds",
    "market_source",
    "require_confluence",
    "avoid_volatile",
]


def create_app(controller, auth: AdminAuth | None = None) -> FastAPI:
    settings = controller.settings
    auth = auth or AdminAuth(
        username=settings.web_admin_username,
        password=settings.web_admin_password,
        cookie_name=settings.web_cookie_name,
        ttl_hours=settings.web_session_ttl_hours,
    )

    app = FastAPI(
        title="HACKER GenAI+",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    def _authed(request: Request) -> bool:
        return auth.check(request.cookies.get(auth.cookie_name))

    def _redirect(msg: str, tab: str = "overview") -> RedirectResponse:
        return RedirectResponse(f"/admin?tab={quote(tab)}&msg={quote(msg)}", status_code=303)

    # ------------------------------------------------------------- public
    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> HTMLResponse:
        del request
        status = await controller.status()
        signals = await controller.recent_signals(10)
        return HTMLResponse(home(status, signals))

    @app.get("/signals", response_class=HTMLResponse)
    async def feed(request: Request) -> HTMLResponse:
        del request
        signals = await controller.recent_signals(100)
        return HTMLResponse(signals_page(signals))

    @app.get("/healthz")
    async def healthz() -> JSONResponse:
        status = await controller.status()
        return JSONResponse(
            {
                "status": "ok",
                "bot_running": status["running"],
                "telegram_configured": status["telegram_configured"],
                "signals_enabled": status["signals_enabled"],
                "uptime_seconds": round(status["uptime_seconds"], 1),
                "version": status["version"],
            }
        )

    @app.get("/api/status")
    async def api_status() -> JSONResponse:
        return JSONResponse(await controller.status())

    @app.get("/api/signals")
    async def api_signals(limit: int = 50) -> JSONResponse:
        return JSONResponse(await controller.recent_signals(limit))

    # -------------------------------------------------------------- auth
    @app.get("/login", response_class=HTMLResponse)
    async def login_get(request: Request) -> HTMLResponse:
        if _authed(request):
            return RedirectResponse("/admin", status_code=303)
        return HTMLResponse(login_page(enabled=auth.enabled))

    @app.post("/login")
    async def login_post(request: Request):
        form = await request.form()
        username = str(form.get("username") or "")
        password = str(form.get("password") or "")
        if auth.verify(username, password):
            token = auth.issue()
            resp = RedirectResponse("/admin", status_code=303)
            resp.set_cookie(
                auth.cookie_name,
                token,
                httponly=True,
                samesite="lax",
                max_age=auth.ttl_seconds,
            )
            return resp
        return HTMLResponse(login_page("Invalid credentials.", enabled=auth.enabled))

    @app.post("/logout")
    async def logout(request: Request) -> RedirectResponse:
        auth.revoke(request.cookies.get(auth.cookie_name))
        resp = RedirectResponse("/login", status_code=303)
        resp.delete_cookie(auth.cookie_name)
        return resp

    # -------------------------------------------------------------- admin
    @app.get("/admin", response_class=HTMLResponse)
    async def admin(request: Request, msg: str = ""):
        if not _authed(request):
            return RedirectResponse("/login", status_code=303)
        status = await controller.status()
        users = await controller.list_users()
        signals = await controller.recent_signals(100)
        settings = await controller.current_settings()
        audit = await controller.audit_log(100)
        return HTMLResponse(admin_page(status, users, signals, settings, audit, msg))

    def _guard(request: Request) -> None:
        if not _authed(request):
            raise HTTPException(status_code=401, detail="unauthorized")

    @app.post("/api/admin/bot")
    async def admin_bot(request: Request) -> RedirectResponse:
        _guard(request)
        form = await request.form()
        action = str(form.get("action") or "")
        if action == "start":
            ok = await controller.start_bot()
            return _redirect("Bot started." if ok else "Telegram not configured.", "bot")
        if action == "stop":
            await controller.stop()
            return _redirect("Bot stopped.", "bot")
        if action == "restart":
            ok = await controller.restart_bot()
            return _redirect(
                "Bot restarted." if ok else "Telegram not configured.", "bot"
            )
        return _redirect("Unknown action.", "bot")

    @app.post("/api/admin/signals")
    async def admin_signals(request: Request) -> RedirectResponse:
        _guard(request)
        form = await request.form()
        value = str(form.get("enabled") or "on").lower() in ("on", "1", "true", "yes")
        enabled = await controller.set_signals_enabled(value)
        return _redirect(
            f"Signal delivery {'ENABLED' if enabled else 'DISABLED'}.", "bot"
        )

    @app.post("/api/admin/ping")
    async def admin_ping(request: Request) -> RedirectResponse:
        _guard(request)
        ok = await controller.send_deploy_notification()
        return _redirect(
            "Deploy ping sent to channel." if ok else "Could not send ping (Telegram not configured).",
            "bot",
        )

    @app.post("/api/admin/generate")
    async def admin_generate(request: Request) -> RedirectResponse:
        _guard(request)
        form = await request.form()
        pair = str(form.get("pair") or "USDBDT-OTC")
        timeframe = str(form.get("timeframe") or "1m")
        try:
            signal = await controller.generate_and_dispatch(pair, timeframe)
        except Exception as exc:  # noqa: BLE001
            return _redirect(f"Error generating signal: {exc}", "overview")
        if signal is None:
            return _redirect("AI verdict: NO TRADE (no setup passed all gates).", "overview")
        return _redirect(
            f"Signal sent: {signal.pair} {signal.direction.value} {signal.timeframe.value} "
            f"({signal.confidence:.0f}%).",
            "overview",
        )

    @app.post("/api/admin/broadcast")
    async def admin_broadcast(request: Request) -> RedirectResponse:
        _guard(request)
        form = await request.form()
        text = str(form.get("text") or "")
        ok = await controller.broadcast(text)
        return _redirect(
            "Broadcast sent." if ok else "Broadcast failed (empty text or Telegram not configured).",
            "overview",
        )

    @app.post("/api/admin/settings")
    async def admin_settings(request: Request) -> RedirectResponse:
        _guard(request)
        form = await request.form()
        for key in _EDITABLE_SETTINGS:
            if key in form:
                await controller.set_setting(key, str(form.get(key) or ""))
        if "signals_enabled" in form:
            value = str(form.get("signals_enabled") or "on").lower() in (
                "on", "1", "true", "yes",
            )
            await controller.set_signals_enabled(value)
        return _redirect("Settings saved and applied.", "settings")

    @app.post("/api/admin/users")
    async def admin_users(request: Request) -> RedirectResponse:
        _guard(request)
        form = await request.form()
        raw_id = str(form.get("telegram_id") or "")
        if not raw_id.isdigit():
            return _redirect("Invalid user id.", "users")
        telegram_id = int(raw_id)
        level = str(form.get("level") or "FREE").upper()
        banned = str(form.get("banned") or "0") == "1"
        await controller.set_user_level(telegram_id, level)
        await controller.set_user_banned(telegram_id, banned)
        return _redirect(f"User {telegram_id} updated.", "users")

    # ----------------------------------------------------- admin JSON reads
    @app.get("/api/admin/logs")
    async def admin_logs(request: Request) -> JSONResponse:
        _guard(request)
        return JSONResponse({"logs": controller.logs(200)})

    @app.get("/api/admin/audit")
    async def admin_audit(request: Request) -> JSONResponse:
        _guard(request)
        return JSONResponse(await controller.audit_log(200))

    @app.get("/favicon.ico")
    async def favicon() -> HTMLResponse:
        return HTMLResponse(status_code=204)

    return app
