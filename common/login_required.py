from functools import wraps
from flask import redirect, session, url_for

def solvingteam(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login.login"))
        if "usertype" not in session or session["usertype"] != "solvingteam":
            return redirect(url_for("login.wrongusertype"))
        return f(*args, **kwargs)
    return decorated_function

def writingteam(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login.login"))
        if "usertype" not in session or session["usertype"] != "writingteam":
            return redirect(url_for("login.wrongusertype"))
        return f(*args, **kwargs)
    return decorated_function
