from flask import Flask, Response, request
import os
from functools import wraps
import hashlib
import outbit.cli.api
import json
import datetime
from ldap3 import Server, Connection, LDAPSocketOpenError


app = Flask(__name__)
app.secret_key = os.urandom(24)


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    valid_auth = False

    # Hash of password provided
    m = hashlib.md5()
    m.update(password)
    password_md5 = m.hexdigest()

    # Check If Local User Can Be Authenticated
    post = outbit.cli.api.db.users.find_one({"username": username})
    if "password_md5" in post and post["password_md5"] == password_md5:
        valid_auth = True

    # LDAP Auth, if Local User Not Authenticated
    if valid_auth == False and outbit.cli.api.ldap_server is not None and outbit.cli.api.ldap_user_cn is not None:
        try:
            server = Server(outbit.cli.api.ldap_server, use_ssl=outbit.cli.api.ldap_use_ssl)
            conn = Connection(server, "uid=%s, %s" % (username, outbit.cli.api.ldap_user_cn), password)
            bind_success = conn.bind()
            if  bind_success == True:
                valid_auth = True
        except LDAPSocketOpenError:
            print("Failed to connect to LDAP server %s" % ldap_server)

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


@app.route("/", methods=["POST"])
@requires_auth
def outbit_base():
    indata = request.get_json()
    dat = None
    status = 200
    username = request.authorization.username

    # Encrypt indata values that are sensitive
    outbit.cli.api.encrypt_dict(indata["options"])

    # Run Action
    dat = outbit.cli.api.parse_action(username, indata["category"], indata["action"], indata["options"])
    if dat is None:
        dat = json.dumps({"response": "  action not found"})

    # Audit Logging / History
    outbit.cli.api.log_action(username, {"result": dat, "category": indata["category"], "action": indata["action"], "options": indata["options"]})

    # http response
    resp = Response(response=dat, status=status, mimetype="application/json")
    return(resp)