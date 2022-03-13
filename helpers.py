import requests
from flask import request, render_template
from functools import wraps


def shorten_str(str):
    result = str.split("(")[0].split("-")[0]
    return result

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.cookies.get('user') == '' or not request.cookies.get('user'):
            return render_template("landing.html", error='')
        return f(*args, **kwargs)

    return decorated_function
