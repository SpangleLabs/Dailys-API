import json
from functools import wraps

from flask import request, abort

with open("config.json", "r") as f:  # TODO: this ain't ideal
    CONFIG = json.load(f)


def get_auth_key(key_name):
    if 'Authorization' in request.headers:
        return request.headers["Authorization"]
    if key_name in request.form:
        return request.form[key_name]
    if key_name in request.cookies:
        return request.cookies[key_name]
    return None


def edit_auth_required(func):
    @wraps(func)
    def decorated_func(*args, **kws):
        if not CONFIG.get("edit_auth_key"):
            return func(*args, **kws)
        # Check key has been given somehow
        key_given = get_auth_key("edit_auth_key")
        if key_given is None:
            abort(401)
        # If auth given isn't edit auth, don't allow
        if key_given != CONFIG["edit_auth_key"]:
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
        key_given = get_auth_key("view_auth_key")
        if key_given is None:
            abort(401)
        # If auth given isn't view auth, and isn't edit auth, don't allow
        valid_keys = [CONFIG.get(key) for key in ["view_auth_key", "edit_auth_key"] if CONFIG.get(key) is not None]
        if key_given not in valid_keys:
            abort(401)
        return func(*args, **kws)
    return decorated_func
