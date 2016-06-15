from flask import Flask, Response, request
import os
from functools import wraps
import hashlib
import outbit.cli.api
import json
import datetime


app = Flask(__name__)
app.secret_key = os.urandom(24)


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    valid_auth = False
    m = hashlib.md5()
    m.update(password)
    password_md5 = m.hexdigest()

    post = outbit.cli.api.db.users.find_one({"username": username})

    if "password_md5" in post and post["password_md5"] == password_md5:
        valid_auth = True

    return valid_auth


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


def log_action(username, post):
    if post["category"] is not None and post["action"] is not None:
        if post["options"] is not None:
            # Filter sensitive information from options
            for option in ["password", "secret"]:
                if option in post["options"]:
                    post["options"][option] = "..."
        # Only Log Valid Requests
        post["date"] = datetime.datetime.utcnow()
        post["user"] = username
        outbit.cli.api.db.logs.insert_one(post)


@app.route("/", methods=["POST"])
@requires_auth
def outbit_base():
    indata = request.get_json()
    dat = None
    status = 200
    username = request.authorization.username

    # Run Action
    dat = outbit.cli.api.parse_action(username, indata["category"], indata["action"], indata["options"])
    if dat is None:
        # TESTING
        print("Testing: %s" % indata)
        dat = json.dumps({"response": "  action not found"})
        # END TESTING
        #status=403 TODO PUT THIS BACK AND REMOVE TESTING

    # Audit Logging / History
    log_action(username, {"result": dat, "category": indata["category"], "action": indata["action"], "options": indata["options"]})

    # http response
    resp = Response(response=dat, status=status, mimetype="application/json")
    return(resp)