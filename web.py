import os
import json
import asyncio
import secrets
from functools import wraps
from urllib.parse import urlencode
from datetime import datetime, timezone, timedelta

import requests
from flask import (Flask, redirect, request, session, render_template,
                   url_for, jsonify, abort)
from dotenv import load_dotenv

load_dotenv()

def _env_str(key, default=""):
    v = os.getenv(key)
    if v is None:
        return default
    return str(v).strip().strip('"').strip("'")

CLIENT_ID = _env_str("DISCORD_CLIENT_ID", "")
CLIENT_SECRET = _env_str("DISCORD_CLIENT_SECRET", "")
REDIRECT_URI = _env_str("DISCORD_REDIRECT_URI", "http://localhost:5000/callback")
SECRET_KEY = _env_str("WEB_SECRET_KEY", "change-me-please-1234567890")
WEB_PORT = int(_env_str("WEB_PORT", "5000") or "5000")
TARGET_GUILD_ID = int(_env_str("TARGET_GUILD_ID", "0") or "0")

ADMIN_ROLE_ID = int(_env_str("ADMIN_ROLE_ID", "0") or "0")
CREATOR_ROLE_ID = int(_env_str("CREATOR_ROLE_ID", "0") or "0")
MODERATOR_ROLE_ID = int(_env_str("MODERATOR_ROLE_ID", "0") or "0")
TICKET_MODERATOR_ROLE_ID = int(_env_str("TICKET_MODERATOR_ROLE_ID", "0") or "0")

ALLOWED_ROLE_IDS = {ADMIN_ROLE_ID, CREATOR_ROLE_ID, MODERATOR_ROLE_ID, TICKET_MODERATOR_ROLE_ID}
ADMIN_ONLY_ROLE_IDS = {ADMIN_ROLE_ID, CREATOR_ROLE_ID}

WEB_AUDIT_FILE = "web_audit.json"

_bot = None
_action_handlers = {}


def set_bot(bot):
    global _bot
    _bot = bot


def register_handler(name, handler):
    _action_handlers[name] = handler


def run_async(coro, timeout=20):
    if _bot is None:
        raise RuntimeError("Bot not attached")
    fut = asyncio.run_coroutine_threadsafe(coro, _bot.loop)
    return fut.result(timeout=timeout)


def call_action(name, **kwargs):
    h = _action_handlers.get(name)
    if not h:
        return False, f"handler '{name}' not found"
    try:
        result = h(**kwargs)
        if asyncio.iscoroutine(result):
            result = run_async(result)
        return True, result
    except Exception as e:
        return False, str(e)


def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default


def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception:
        return False


def load_tickets():
    d = load_json("tickets.json", {"tickets": []})
    return d.get("tickets", []) if isinstance(d, dict) else []


def load_tikets():
    d = load_json("tikets.json", {"tikets": []})
    return d.get("tikets", []) if isinstance(d, dict) else []


def load_punishments():
    d = load_json("punishment_appeals.json", {"appeals": []})
    return d.get("appeals", []) if isinstance(d, dict) else []


def load_counter():
    d = load_json("global_counter.json", {"counter": 0})
    return d.get("counter", 0)


def load_warns():
    return load_json("warns.json", {})


def load_audit():
    d = load_json(WEB_AUDIT_FILE, {"logs": []})
    return d.get("logs", []) if isinstance(d, dict) else []


def append_audit(user, action, details=""):
    d = load_json(WEB_AUDIT_FILE, {"logs": []})
    if not isinstance(d, dict):
        d = {"logs": []}
    d.setdefault("logs", [])
    d["logs"].append({
        "user": user,
        "action": action,
        "details": details,
        "time": datetime.now(timezone.utc).timestamp(),
    })
    if len(d["logs"]) > 5000:
        d["logs"] = d["logs"][-5000:]
    save_json(WEB_AUDIT_FILE, d)


def get_allowed_roles_for_user(roles):
    return bool(set(roles) & ALLOWED_ROLE_IDS)


def is_admin_session():
    u = session.get("user")
    if not u:
        return False
    return bool(set(u.get("roles", [])) & ADMIN_ONLY_ROLE_IDS)


def fetch_user_from_discord(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        u = requests.get("https://discord.com/api/users/@me", headers=headers, timeout=10)
        if u.status_code != 200:
            return None, None
        user = u.json()
        m = requests.get(
            f"https://discord.com/api/users/@me/guilds/{TARGET_GUILD_ID}/member",
            headers=headers, timeout=10,
        )
        if m.status_code != 200:
            return user, None
        return user, m.json()
    except Exception:
        return None, None


def is_logged_in():
    return "user" in session


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            if request.path.startswith("/api/"):
                return jsonify({"error": "unauthorized"}), 401
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not is_logged_in() or not is_admin_session():
            if request.path.startswith("/api/"):
                return jsonify({"error": "forbidden"}), 403
            abort(403)
        return f(*args, **kwargs)
    return wrapper


def current_user():
    return session.get("user")


def build_avatar_url(user):
    if not user or not user.get("avatar"):
        return "https://cdn.discordapp.com/embed/avatars/0.png"
    return f"https://cdn.discordapp.com/avatars/{user['id']}/{user['avatar']}.png"


def ts_to_str(ts):
    if not ts:
        return "—"
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc).strftime("%d.%m.%Y %H:%M")
    except Exception:
        return "—"


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = SECRET_KEY
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = False
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)

    @app.context_processor
    def inject_globals():
        u = current_user()
        return {
            "current_user": u,
            "avatar_url": build_avatar_url(u) if u else None,
            "is_admin": is_admin_session(),
            "ts_to_str": ts_to_str,
        }

    # ---------- AUTH ----------
    @app.route("/login")
    def login():
        if is_logged_in():
            return redirect(url_for("dashboard"))
        state = secrets.token_urlsafe(24)
        session["oauth_state"] = state
        session.permanent = True
        params = {
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": "identify guilds.members.read",
            "state": state,
            "prompt": "consent",
        }
        return redirect("https://discord.com/api/oauth2/authorize?" + urlencode(params))

    @app.route("/callback")
    def callback():
        code = request.args.get("code")
        if not code:
            return "No code provided", 400

        data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
        }
        try:
            r = requests.post(
                "https://discord.com/api/oauth2/token",
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10,
            )
        except Exception as e:
            return f"Request failed: {e}", 500

        if r.status_code != 200:
            return f"Token exchange failed: {r.text}", 400

        tokens = r.json()
        user, member = fetch_user_from_discord(tokens["access_token"])
        if not user or not member:
            return "You are not a member of the target guild", 403

        roles = [int(x) for x in member.get("roles", [])]
        if not get_allowed_roles_for_user(roles):
            return "Access denied — insufficient role", 403

        session["user"] = {
            "id": user["id"],
            "username": user["username"],
            "global_name": user.get("global_name"),
            "avatar": user.get("avatar"),
            "roles": roles,
            "access_token": tokens.get("access_token"),
        }
        session.pop("oauth_state", None)
        append_audit(user["username"], "login", "Вход в панель")
        return redirect(url_for("dashboard"))

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    # ---------- PAGES ----------
    @app.route("/")
    @login_required
    def dashboard():
        tickets = load_tickets()
        tikets = load_tikets()
        punishments = load_punishments()

        open_tickets = sum(1 for t in tickets if t.get("status") == "open")
        closed_tickets = sum(1 for t in tickets if t.get("status") == "closed")
        open_tikets = sum(1 for t in tikets if t.get("status") == "open")
        closed_tikets = sum(1 for t in tikets if t.get("status") == "closed")

        guild_stats = {"members": 0, "online": 0, "boosters": 0, "roles": 0, "channels": 0}
        if _bot:
            g = _bot.get_guild(TARGET_GUILD_ID)
            if g:
                guild_stats["members"] = g.member_count or 0
                guild_stats["online"] = sum(1 for m in g.members if not m.bot)
                guild_stats["boosters"] = g.premium_subscription_count or 0
                guild_stats["roles"] = len(g.roles)
                guild_stats["channels"] = len(g.channels)

        stats = {
            "tickets_total": len(tickets),
            "tickets_open": open_tickets,
            "tickets_closed": closed_tickets,
            "tikets_total": len(tikets),
            "tikets_open": open_tikets,
            "tikets_closed": closed_tikets,
            "punishments_total": len(punishments),
            "punishments_appeals": sum(1 for p in punishments if p.get("appeal")),
            "total_issued": load_counter(),
            **guild_stats,
        }

        recent_punishments = sorted(punishments, key=lambda x: x.get("date", 0), reverse=True)[:5]
        recent_tickets = sorted(tickets, key=lambda x: x.get("created_at", 0), reverse=True)[:5]

        return render_template(
            "dashboard.html",
            stats=stats,
            recent_punishments=recent_punishments,
            recent_tickets=recent_tickets,
            active_page="dashboard",
        )

    @app.route("/tickets")
    @login_required
    def tickets():
        items = sorted(load_tickets(), key=lambda x: x.get("created_at", 0), reverse=True)
        return render_template(
            "tickets.html", title="Жалобы", items=items,
            kind="complaint", active_page="tickets",
        )

    @app.route("/tikets")
    @login_required
    def tikets():
        items = sorted(load_tikets(), key=lambda x: x.get("created_at", 0), reverse=True)
        return render_template(
            "tickets.html", title="Тикеты", items=items,
            kind="tiket", active_page="tikets",
        )

    @app.route("/punishments")
    @login_required
    def punishments():
        items = sorted(load_punishments(), key=lambda x: x.get("date", 0), reverse=True)
        return render_template(
            "punishments.html", items=items, active_page="punishments",
        )

    @app.route("/users")
    @login_required
    def users():
        warns = load_warns()
        guild_id_key = str(TARGET_GUILD_ID)
        user_warns = warns.get(guild_id_key, {}) if isinstance(warns, dict) else {}
        users_data = []
        for uid, list_warns in user_warns.items():
            if not list_warns:
                continue
            users_data.append({"id": uid, "warns_count": len(list_warns), "warns": list_warns})
        users_data.sort(key=lambda x: x["warns_count"], reverse=True)
        return render_template("users.html", users=users_data, active_page="users")

    @app.route("/raid")
    @login_required
    def raid():
        status = "unknown"
        try:
            import golos
            g = _bot.get_guild(TARGET_GUILD_ID) if _bot else None
            if g:
                status = golos.get_raid_status(g.id).get("status", "unknown")
        except Exception:
            pass
        return render_template("raid.html", status=status, active_page="raid")

    @app.route("/broadcast")
    @login_required
    @admin_required
    def broadcast():
        return render_template("broadcast.html", active_page="broadcast")

    @app.route("/logs")
    @login_required
    def logs():
        items = list(reversed(load_audit()))
        return render_template("logs.html", items=items, active_page="logs")

    # ---------- API ----------
    @app.route("/api/stats")
    @login_required
    def api_stats():
        tickets = load_tickets()
        tikets = load_tikets()
        punishments = load_punishments()

        days_labels = []
        tickets_daily = []
        punishments_daily = []
        now = datetime.now(timezone.utc)
        for i in range(6, -1, -1):
            day = now - timedelta(days=i)
            start = day.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
            end = start + 86400
            days_labels.append(day.strftime("%d.%m"))
            tickets_daily.append(sum(1 for t in tickets if start <= t.get("created_at", 0) < end))
            punishments_daily.append(sum(1 for p in punishments if start <= p.get("date", 0) < end))

        types_counts = {}
        for p in punishments:
            tp = p.get("type", "unknown")
            types_counts[tp] = types_counts.get(tp, 0) + 1

        return jsonify({
            "days": days_labels,
            "tickets_daily": tickets_daily,
            "punishments_daily": punishments_daily,
            "types": types_counts,
        })

    @app.route("/api/ticket/<kind>/<path:item_id>/verdict", methods=["POST"])
    @login_required
    def api_ticket_verdict(kind, item_id):
        data = request.get_json(silent=True) or {}
        verdict = (data.get("verdict") or "").strip()
        if not verdict:
            return jsonify({"error": "empty verdict"}), 400
        ok, res = call_action("ticket_verdict", kind=kind, item_id=item_id,
                             verdict=verdict, moderator_id=current_user()["id"])
        append_audit(current_user()["username"], "ticket_verdict",
                     f"{kind} {item_id} → {verdict[:50]}")
        return jsonify({"ok": ok, "result": str(res)})

    @app.route("/api/ticket/<kind>/<path:item_id>/delete", methods=["POST"])
    @login_required
    @admin_required
    def api_ticket_delete(kind, item_id):
        data = request.get_json(silent=True) or {}
        reason = (data.get("reason") or "Не указана").strip()
        ok, res = call_action("ticket_delete", kind=kind, item_id=item_id, reason=reason)
        append_audit(current_user()["username"], "ticket_delete",
                     f"{kind} {item_id} — {reason[:50]}")
        return jsonify({"ok": ok, "result": str(res)})

    @app.route("/api/ticket/<kind>/<path:item_id>/delete_verdict", methods=["POST"])
    @login_required
    @admin_required
    def api_ticket_delete_verdict(kind, item_id):
        ok, res = call_action("ticket_delete_verdict", kind=kind, item_id=item_id)
        append_audit(current_user()["username"], "ticket_delete_verdict",
                     f"{kind} {item_id}")
        return jsonify({"ok": ok, "result": str(res)})

    @app.route("/api/punishment/<path:item_id>/appeal_verdict", methods=["POST"])
    @login_required
    @admin_required
    def api_punishment_appeal_verdict(item_id):
        data = request.get_json(silent=True) or {}
        verdict = (data.get("verdict") or "").strip()
        if not verdict:
            return jsonify({"error": "empty verdict"}), 400
        ok, res = call_action("punishment_appeal_verdict", item_id=item_id,
                             verdict=verdict, moderator_id=current_user()["id"],
                             moderator_name=current_user().get("global_name") or current_user()["username"])
        append_audit(current_user()["username"], "punishment_appeal_verdict",
                     f"{item_id} → {verdict[:50]}")
        return jsonify({"ok": ok, "result": str(res)})

    @app.route("/api/punishment/<path:item_id>/delete_verdict", methods=["POST"])
    @login_required
    @admin_required
    def api_punishment_delete_verdict(item_id):
        ok, res = call_action("punishment_delete_verdict", item_id=item_id)
        append_audit(current_user()["username"], "punishment_delete_verdict", item_id)
        return jsonify({"ok": ok, "result": str(res)})

    @app.route("/api/user/<int:user_id>/warns/clear", methods=["POST"])
    @login_required
    @admin_required
    def api_clear_warns(user_id):
        ok, res = call_action("clear_warns", user_id=user_id)
        append_audit(current_user()["username"], "clear_warns", str(user_id))
        return jsonify({"ok": ok, "result": str(res)})

    @app.route("/api/warn", methods=["POST"])
    @login_required
    def api_warn():
        data = request.get_json(silent=True) or {}
        try:
            user_id = int(data.get("user_id"))
        except Exception:
            return jsonify({"error": "bad user_id"}), 400
        reason = (data.get("reason") or "").strip()
        if not reason:
            return jsonify({"error": "empty reason"}), 400
        ok, res = call_action("warn", user_id=user_id, reason=reason,
                             moderator_id=current_user()["id"],
                             moderator_name=current_user().get("global_name") or current_user()["username"])
        append_audit(current_user()["username"], "warn", f"<@{user_id}> — {reason[:50]}")
        return jsonify({"ok": ok, "result": str(res)})

    @app.route("/api/mute", methods=["POST"])
    @login_required
    def api_mute():
        data = request.get_json(silent=True) or {}
        try:
            user_id = int(data.get("user_id"))
            minutes = int(data.get("minutes", 30))
        except Exception:
            return jsonify({"error": "bad args"}), 400
        reason = (data.get("reason") or "").strip()
        if not reason:
            return jsonify({"error": "empty reason"}), 400
        ok, res = call_action("mute", user_id=user_id, minutes=minutes, reason=reason,
                             moderator_id=current_user()["id"],
                             moderator_name=current_user().get("global_name") or current_user()["username"])
        append_audit(current_user()["username"], "mute",
                     f"<@{user_id}> {minutes}м — {reason[:50]}")
        return jsonify({"ok": ok, "result": str(res)})

    @app.route("/api/kick", methods=["POST"])
    @login_required
    @admin_required
    def api_kick():
        data = request.get_json(silent=True) or {}
        try:
            user_id = int(data.get("user_id"))
        except Exception:
            return jsonify({"error": "bad user_id"}), 400
        reason = (data.get("reason") or "").strip()
        if not reason:
            return jsonify({"error": "empty reason"}), 400
        ok, res = call_action("kick", user_id=user_id, reason=reason,
                             moderator_id=current_user()["id"],
                             moderator_name=current_user().get("global_name") or current_user()["username"])
        append_audit(current_user()["username"], "kick", f"<@{user_id}> — {reason[:50]}")
        return jsonify({"ok": ok, "result": str(res)})

    @app.route("/api/ban", methods=["POST"])
    @login_required
    @admin_required
    def api_ban():
        data = request.get_json(silent=True) or {}
        try:
            user_id = int(data.get("user_id"))
        except Exception:
            return jsonify({"error": "bad user_id"}), 400
        reason = (data.get("reason") or "").strip()
        if not reason:
            return jsonify({"error": "empty reason"}), 400
        ok, res = call_action("ban", user_id=user_id, reason=reason,
                             moderator_id=current_user()["id"],
                             moderator_name=current_user().get("global_name") or current_user()["username"])
        append_audit(current_user()["username"], "ban", f"<@{user_id}> — {reason[:50]}")
        return jsonify({"ok": ok, "result": str(res)})

    @app.route("/api/unban", methods=["POST"])
    @login_required
    @admin_required
    def api_unban():
        data = request.get_json(silent=True) or {}
        try:
            user_id = int(data.get("user_id"))
        except Exception:
            return jsonify({"error": "bad user_id"}), 400
        reason = (data.get("reason") or "Не указана").strip()
        ok, res = call_action("unban", user_id=user_id, reason=reason)
        append_audit(current_user()["username"], "unban", str(user_id))
        return jsonify({"ok": ok, "result": str(res)})

    @app.route("/api/lockdown", methods=["POST"])
    @login_required
    def api_lockdown():
        ok, res = call_action("lockdown")
        append_audit(current_user()["username"], "lockdown", "")
        return jsonify({"ok": ok, "result": str(res)})

    @app.route("/api/unlockdown", methods=["POST"])
    @login_required
    def api_unlockdown():
        ok, res = call_action("unlockdown")
        append_audit(current_user()["username"], "unlockdown", "")
        return jsonify({"ok": ok, "result": str(res)})

    @app.route("/api/broadcast", methods=["POST"])
    @login_required
    @admin_required
    def api_broadcast():
        data = request.get_json(silent=True) or {}
        channel_id = str(data.get("channel_id") or "").strip()
        content = (data.get("content") or "").strip()
        title = (data.get("title") or "").strip()
        role_id = str(data.get("role_id") or "").strip()
        if not channel_id:
            return jsonify({"error": "bad channel_id"}), 400
        ok, res = call_action("broadcast", channel_id=channel_id, content=content or None,
                             embed_title=title or None, role_id=role_id or None)
        append_audit(current_user()["username"], "broadcast", f"#{channel_id}")
        return jsonify({"ok": ok, "result": str(res)})

    @app.route("/api/guild/member/<int:user_id>")
    @login_required
    def api_member(user_id):
        if not _bot:
            return jsonify({"error": "bot offline"}), 503
        g = _bot.get_guild(TARGET_GUILD_ID)
        if not g:
            return jsonify({"error": "guild not found"}), 404
        m = g.get_member(user_id)
        if not m:
            return jsonify({"error": "member not found"}), 404
        return jsonify({
            "id": m.id,
            "name": str(m),
            "display_name": m.display_name,
            "avatar": m.display_avatar.url,
            "joined_at": m.joined_at.timestamp() if m.joined_at else None,
            "top_role": m.top_role.name,
            "roles": [r.name for r in m.roles if r.name != "@everyone"],
            "is_bot": m.bot,
            "status": str(m.status),
        })

    return app


def start_web_thread():
    import threading
    app = create_app()

    def _run():
        app.run(host="0.0.0.0", port=WEB_PORT, debug=False,
                use_reloader=False, threaded=True)

    t = threading.Thread(target=_run, daemon=True, name="web-dashboard")
    t.start()
    print(f"🌐 Веб-панель запущена на http://localhost:{WEB_PORT}")
    return t