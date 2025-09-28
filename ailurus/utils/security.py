from ailurus.utils.config import get_config
from ailurus.models import Team
from flask import jsonify, request
from flask_jwt_extended import current_user, verify_jwt_in_request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from typing import Optional


def jwt_rate_limit_key():
    verify_jwt_in_request(optional=True)
    if current_user is not None:
        return f"team:{current_user.id}"
    return get_remote_address()


limiter = Limiter(key_func=jwt_rate_limit_key, default_limits=[])


def rate_limit_response(e):
    return (
        jsonify(
            status="too many request",
            message="no bruteforce needed, calm down a little bit.",
        ),
        429,
    )


current_team: Optional[Team] = current_user


def admin_only():
    # Preflight
    if request.method == "OPTIONS":
        return
    req_secret = request.headers.get("x-admin-secret", None)

    # If server admin forgot to set ADMIN_SECRET, all request to the admin API are forbid
    if get_config("ADMIN_SECRET") is None or req_secret != get_config("ADMIN_SECRET"):
        return jsonify(status="forbidden", message="forbidden."), 403


def worker_only():
    # Preflight
    if request.method == "OPTIONS":
        return
    req_secret = request.headers.get("x-worker-secret", None)

    # If server admin forgot to set ADMIN_SECRET, all request to the admin API are forbid
    if get_config("WORKER_SECRET") is None or req_secret != get_config("WORKER_SECRET"):
        return jsonify(status="forbidden", message="forbidden."), 403


def checkeragent_only():
    # Preflight
    if request.method == "OPTIONS":
        return
    req_secret = request.headers.get("x-CHECKER-secret", None)

    # If server admin forgot to set ADMIN_SECRET, all request to the admin API are forbid
    if get_config("CHECKER_AGENT_SECRET") is None or req_secret != get_config(
        "CHECKER_AGENT_SECRET"
    ):
        return jsonify(status="forbidden", message="forbidden."), 403


def validteam_only():
    # Preflight
    if request.method == "OPTIONS":
        return

    verify_jwt_in_request()
    if current_team is None:
        return jsonify(status="forbidden", message="forbidden."), 403


def svcmode_match_only(svcmode_name):
    def wrapper_func():
        # Preflight
        if request.method == "OPTIONS":
            return
        if get_config("SERVICE_MODE") != svcmode_name:
            return jsonify(status="forbidden", message="forbidden."), 403

    return wrapper_func
