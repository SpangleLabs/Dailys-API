import json
from functools import wraps

from flask import request, abort

with open("config.json", "r") as f:  # TODO: this ain't ideal
    CONFIG = json.load(f)


def edit_auth_required(func):
    @wraps(func)
    def decorated_func(*args, **kws):
        if not CONFIG.get("edit_auth_key"):
            return func(*args, **kws)
        if 'Authorization' not in request.headers:
            abort(401)
        if request.headers['Authorization'] != CONFIG["edit_auth_key"]:
            abort(401)
        return func(*args, **kws)
    return decorated_func


def view_auth_required(func):
    @wraps(func)
    def decorated_func(*args, **kws):
        # If view auth isn't set, don't check
        if not CONFIG.get("view_auth_key"):
            return func(*args, **kws)
        # Check key has been given, somehow
        if 'Authorization' not in request.headers:
            if "view_auth_key" not in request.form:
                abort(401)
                return
            else:
                key_given = request.form["view_auth_key"]
        else:
            key_given = request.headers["Authorization"]
        # If auth given isn't view auth, and isn't edit auth, don't allow
        valid_keys = [CONFIG.get(key) for key in ["view_auth_key", "edit_auth_key"] if CONFIG.get(key) is not None]
        if key_given not in valid_keys:
            abort(401)
        return func(*args, **kws)
    return decorated_func
