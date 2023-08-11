from flask import jsonify, request

def admin_only():
    req_secret = request.headers.get("x-adce-secret", None)
    if req_secret != "SecretS":
        return jsonify(status="forbidden", message="forbidden."), 403