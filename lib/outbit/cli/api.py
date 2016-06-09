""" Command Line Interface Module """
import optparse
import sys
import os
import json
import hashlib
from functools import wraps
from flask import Flask, Response, request
from pymongo import MongoClient


app = Flask(__name__)
app.secret_key = os.urandom(24)

dbclient = MongoClient('localhost', 27017)
db = dbclient.outbit


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    valid_auth = False
    m = hashlib.md5()
    m.update(password)
    password_md5 = m.hexdigest()

    post = db.users.posts.find_one({"username": username})

    if post["password_md5"] == password_md5:
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


def plugin_help(action, options):
    cursor = db.actions.find()
    response = ""
    for dbaction in builtin_actions + list(cursor):
        response += "  %s %s \t\t%-60s\n" % (dbaction["category"].lstrip("/").rstrip("/").replace("/", " "), dbaction["action"], dbaction["desc"])
    return json.dumps({"response": response})


def plugin_ping(action, options):
    return json.dumps({"response": "  pong"})


def plugin_users_add(action, options):
    username = None
    password = None

    for option in options:
        if "username=" in option:
            username = option.split("=")[1]
        if "password=" in option:
            password = option.split("=")[1]

    if username is None or password is None:
        return json.dumps({"response": "  username and password are required options"})
    else:
        result = db.users.posts.find_one({"username": username})
        if result is None:
            m = hashlib.md5()
            m.update(password)
            password_md5 = str(m.hexdigest())
            post = {"username": username, "password_md5": password_md5}
            db.users.posts.insert_one(post)
            return json.dumps({"response": "  created user %s" % username})
        else:
            return json.dumps({"response": "  user %s already exists" % username})


def plugin_users_del(action, options):
    username = None

    for option in options:
        if "username=" in option:
            username = option.split("=")[1]

    post = {"username": username}
    result = db.users.posts.delete_many(post)
    if result.deleted_count > 0:
        return json.dumps({"response": "  deleted user %s" % username})
    else:
        return json.dumps({"response": "  user %s does not exist" % username})


def plugin_users_list(action, options):
    result = ""
    cursor = db.users.posts.find()
    for doc in list(cursor):
        result += "  %s\n" % doc["username"]
    return json.dumps({"response": result.rstrip()}) # Do not return the last character (carrage return)


def plugin_actions_add(action, options):
    post = {}
    post["name"] = ""
    post["desc"] = ""
    post["category"] = ""
    post["action"] = ""
    post["chdir"] = ""
    post["command"] = ""
    dat = None
    for option in options:
        if "name=" in option:
            post["name"] = option.split("=")[1]
        if "desc=" in option:
            post["desc"] = option.split("=")[1]
        if "category=" in option:
            post["category"] = option.split("=")[1]
        if "action=" in option:
            post["action"] = option.split("=")[1]
        if "chdir=" in option:
            post["chdir"] = option.split("=")[1]
        if "command=" in option:
            post["command"] = option.split("=")[1]
    find_result = db.actions.find_one({"name": post["name"]})
    if find_result is None:
        result = db.actions.insert_one(post)
        dat = json.dumps({"response": "  created action %s" % post["name"]})
    else:
        dat = json.dumps({"response": "  action %s already exists" % post["name"]})
    return dat


def plugin_command(action, options):
    return json.dumps({ "response": "command output: %s, args: %s" % (action, options)})


def plugin_actions_del(action, options):
    name = None
    dat = None
    for option in options:
        if "name=" in option:
            name = option.split("=")[1]

    if name is None:
        dat = json.dumps({"response": "  name option is required"})
    post = {"name": name}
    result = db.actions.delete_many(post)
    if result.deleted_count > 0:
        dat = json.dumps({"response": "  deleted action %s" % name})
    else:
        dat = json.dumps({"response": "  action %s does not exist" % name})
    return dat


def plugin_actions_list(action, options):
    result = ""
    cursor = db.actions.find()
    for doc in list(cursor):
        #result += "  %s\n" % doc["name"]
        result += "  %s\n" % doc
    return json.dumps({"response": result.rstrip()}) # Do not return the last character (carrage return)


plugins = {"command": plugin_command,
            "actions_list": plugin_actions_list,
            "actions_del": plugin_actions_del,
            "actions_add": plugin_actions_add,
            "users_list": plugin_users_list,
            "users_del": plugin_users_del,
            "users_add": plugin_users_add,
            "ping": plugin_ping,
            "help": plugin_help}

builtin_actions = [{'category': '/actions', 'plugin': 'actions_list', 'action': 'list', 'desc': 'list actions'},
                  {'category': '/actions', 'plugin': 'actions_del', 'action': 'del', 'desc': 'del actions'},
                  {'category': '/actions', 'plugin': 'actions_add', 'action': 'add', 'desc': 'add actions'},
                  {'category': '/users', 'plugin': 'users_list', 'action': 'list', 'desc': 'list users'},
                  {'category': '/users', 'plugin': 'users_del', 'action': 'del', 'desc': 'del users'},
                  {'category': '/users', 'plugin': 'users_add', 'action': 'add', 'desc': 'add users'},
                  {'category': '/', 'plugin': 'ping', 'action': 'ping', 'desc': 'verify connectivity'},
                  {'category': '/', 'plugin': 'help', 'action': 'help', 'desc': 'print usage'},
                  ]


def parse_action(category, action, options):
    cursor = db.actions.find()
    for dbaction in builtin_actions + list(cursor):
        if dbaction["category"] == category and dbaction["action"] == action:
            if "plugin" in dbaction:
                return plugins[dbaction["plugin"]](dbaction, options)

            for plugin in plugins:
                if plugin in dbaction:
                    return plugins[plugin](dbaction, options)
    return None


@app.route("/", methods=["POST"])
@requires_auth
def outbit_base():
    indata = request.get_json()
    dat = None
    status = 200

    dat = parse_action(indata["category"], indata["action"], indata["options"].split(","))
    if dat is None:
        # TESTING
        print("Testing: %s" % indata)
        dat = json.dumps({"response": "  action not found"})
        # END TESTING
        #status=403 TODO PUT THIS BACK AND REMOVE TESTING

    resp = Response(response=dat, status=status, mimetype="application/json")
    return(resp)


class Cli(object):
    """ outbit CLI """

    def __init__(self):
        """ Setup Arguments and Options for CLI """
        # Parse CLI Arguments
        parser = optparse.OptionParser()
        parser.add_option("-s", "--server", dest="server",
                          help="IP address or hostname of outbit-api server",
                          metavar="SERVER",
                          default="127.0.0.1")
        parser.add_option("-p", "--port", dest="port",
                          help="tcp port of outbit-api server",
                          metavar="PORT",
                          default="8088")
        parser.add_option("-t", "--secure", dest="is_secure",
                          help="Use SSL",
                          metavar="SECURE",
                          action="store_true")
        parser.add_option("-d", "--debug", dest="is_debug",
                          help="Debug Mode",
                          metavar="DEBUG",
                          action="store_true")
        (options, args) = parser.parse_args()
        self.server = options.server
        self.port = int(options.port)
        self.is_secure = options.is_secure
        self.is_debug = options.is_debug

    def run(self):
        """ EntryPoint Of Application """

        # First Time Defaults, Setup superadmin if it doesnt exist
        default_user = "superadmin"
        default_password = "superadmin"
        post = db.users.posts.find_one({"username": default_user})
        if post is None:
            action_add_user(default_user, default_password)

        # Start API Server
        print("Starting outbit api server on %s://%s:%d" % ("https" if
            self.is_secure else "http", self.server, self.port))
        if self.is_secure:
            print("Does not support SSL yet")
            sys.exit(1)
        else:
            app.run(host=self.server, port=self.port, debug=self.is_debug)



