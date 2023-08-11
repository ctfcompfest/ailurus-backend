from flask import jsonify, request
from and_platform.core.config import get_config

def admin_only():
    req_secret = request.headers.get("x-adce-secret", None)

    # If server admin forgot to set ADCE_SECRET, all request to the admin API are forbid
    if get_config("ADCE_SECRET") == None or req_secret != get_config("ADCE_SECRET"):
        return jsonify(status="forbidden", message="forbidden."), 403