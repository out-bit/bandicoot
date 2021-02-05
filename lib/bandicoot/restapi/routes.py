from flask import Flask, Response, request
from flask_cors import CORS, cross_origin
import jwt
import os
from functools import wraps
import hashlib
import bandicoot.cli.api
import json
import datetime
import re
from ldap3 import Server, Connection
from ldap3.core.exceptions import LDAPSocketOpenError


app = Flask(__name__)
CORS(app)
app.secret_key = os.urandom(24)


def rest_request_is_valid(indata):
    """Validate Request"""
    # Verify required dict objects were present
    if indata is None or "options" not in indata or "category" not in indata or "action" not in indata:
        return False
    # Verify type of each
    if not (indata["options"] is None or isinstance(indata["options"], dict)) or not isinstance(indata["category"], basestring) or not isinstance(indata["action"], basestring):
        return False
    # Check options
    if isinstance(indata["options"], dict):
        for option in indata["options"]:
            # Check Key
            if not re.match(r'^[/_a-zA-Z0-9\-]+$', str(option)):
                return False
            # Check Value
            if not re.match(r'^[/_a-zA-Z0-9\*:\.\-=\?\~]+$', str(indata["options"][str(option)])):
                return False
    if not re.match(r'^[a-zA-Z0-9_\-/]+$', indata["category"]):
        return False
    if not re.match(r'^[a-zA-Z0-9_\-]+$', indata["action"]):
        return False

    return True


def create_token(user):
    global app
    payload = {
        # subject
        'sub': user,
        #issued at
        'iat': datetime.datetime.utcnow(),
        #expiry
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
    }
 
    token = jwt.encode(payload, app.secret_key, algorithm='HS256')
    return token.decode('unicode_escape')
 

def parse_token(token):
    global app
    return jwt.decode(token, app.secret_key, algorithms='HS256')


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
    post = bandicoot.cli.api.db.users.find_one({"username": username})
    if post is not None:
        if "password_md5" in post and post["password_md5"] == password_md5:
            valid_auth = True

    # LDAP Auth, if Local User Not Authenticated
    if valid_auth == False and bandicoot.cli.api.ldap_server is not None and bandicoot.cli.api.ldap_user_cn is not None:
        try:
            server = Server(bandicoot.cli.api.ldap_server, use_ssl=bandicoot.cli.api.ldap_use_ssl)
            conn = Connection(server, "uid=%s, %s" % (username, bandicoot.cli.api.ldap_user_cn), password)
            bind_success = conn.bind()
            if  bind_success == True:
                valid_auth = True
        except LDAPSocketOpenError:
            print("Failed to connect to LDAP server %s" % bandicoot.cli.api.ldap_server)

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
        g = f.func_globals
        auth = request.authorization
        data = request.get_json(force=True)
        username = None
        password = None

        if auth is None:
            # user post username/password
            username = data["username"]
            password = data["password"]
        else:
            # username/password from Authorized Headers
            username = auth.username
            password = auth.password

        # Set username for decorated func
        g["username"] = username

        if not check_auth(username, password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        g = f.func_globals

        if not request.headers.get('Authorization'):
            return Response(response="Missing authorization header", status=401)
        try:
            payload = parse_token(request.headers.get('Authorization').split()[1])
        except jwt.DecodeError:
            return Response(response="Token is invalid", status=401)
        except jwt.ExpiredSignature:
            return Response(response="Token has expired", status=401)

        # Set username for decorated func
        g["username"] = payload['sub']

        return f(*args, **kwargs)
    return decorated_function


@app.route("/login", methods=["POST"])
@requires_auth
def bandicoot_login():
    dat = None
    status = 200

    # Authenticate user, return a token
    dat = json.dumps({ "token": create_token(username) })

    # http response
    resp = Response(response=dat, status=status, mimetype="application/json")
    return(resp)


# Support Authorization headers for auth (bandicoot-cli uses this API)
@app.route("/", methods=["POST"])
@requires_auth
def bandicoot_base():
    indata = request.get_json()
    dat = None
    status = 200

    # Error on invalid request
    if not rest_request_is_valid(indata):
        return Response(response=json.dumps({"response": "  invalid request"}), status=400, mimetype="application/json")

    # Encrypt indata values that are sensitive
    bandicoot.cli.api.encrypt_dict(indata["options"])

    # Run Action
    dat = bandicoot.cli.api.parse_action(username, indata["category"], indata["action"], indata["options"])
    if dat is None:
        dat = json.dumps({"response": "  action not found"})

    # Audit Logging / History
    bandicoot.cli.api.log_action(username, {"result": dat, "category": indata["category"], "action": indata["action"], "options": indata["options"]})

    # http response
    resp = Response(response=dat, status=status, mimetype="application/json")
    return(resp)


# Support Token for auth (bandicoot-gui uses this API)
@app.route("/api", methods=["POST"])
@token_required
def bandicoot_api():
    indata = request.get_json()
    dat = None
    status = 200

    # Error on invalid request
    if not rest_request_is_valid(indata):
        return Response(response=json.dumps({"response": "  invalid request"}), status=400, mimetype="application/json")

    # Encrypt indata values that are sensitive
    bandicoot.cli.api.encrypt_dict(indata["options"])

    # Run Action
    dat = bandicoot.cli.api.parse_action(username, indata["category"], indata["action"], indata["options"])
    if dat is None:
        dat = json.dumps({"response": "  action not found"})
        status = 400

    # Audit Logging / History
    bandicoot.cli.api.log_action(username, {"result": dat, "category": indata["category"], "action": indata["action"], "options": indata["options"]})

    # http response
    resp = Response(response=dat, status=status, mimetype="application/json")
    return(resp)
