from flask import Blueprint

admin_route = Blueprint("admin", __name__, url_prefix="/admin")

@admin_route.get("/")
def admin_index():
    pass

@admin_route.get("/login")
def admin_login():
    pass