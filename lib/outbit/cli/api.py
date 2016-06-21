""" Command Line Interface Module """
import optparse
import sys
import os
import yaml
import re
import json
import hashlib
from pymongo import MongoClient
from outbit.restapi import routes
from outbit.plugins import builtins
from Crypto.Cipher import AES
import binascii
from jinja2 import Template
import ssl
import logging
from logging.handlers import RotatingFileHandler


dbclient = MongoClient('localhost', 27017)
db = dbclient.outbit
encryption_password = None


plugins = {"command": builtins.plugin_command,
            "actions_list": builtins.plugin_actions_list,
            "actions_del": builtins.plugin_actions_del,
            "actions_edit": builtins.plugin_actions_edit,
            "actions_add": builtins.plugin_actions_add,
            "users_list": builtins.plugin_users_list,
            "users_del": builtins.plugin_users_del,
            "users_edit": builtins.plugin_users_edit,
            "users_add": builtins.plugin_users_add,
            "roles_list": builtins.plugin_roles_list,
            "roles_del": builtins.plugin_roles_del,
            "roles_edit": builtins.plugin_roles_edit,
            "roles_add": builtins.plugin_roles_add,
            "secrets_list": builtins.plugin_secrets_list,
            "secrets_del": builtins.plugin_secrets_del,
            "secrets_edit": builtins.plugin_secrets_edit,
            "secrets_add": builtins.plugin_secrets_add,
            "plugins_list": builtins.plugin_plugins_list,
            "ping": builtins.plugin_ping,
            "logs": builtins.plugin_logs,
            "help": builtins.plugin_help}

builtin_actions = [{'category': '/actions', 'plugin': 'actions_list', 'action': 'list', 'desc': 'list actions'},
                  {'category': '/actions', 'plugin': 'actions_del', 'action': 'del', 'desc': 'del actions'},
                  {'category': '/actions', 'plugin': 'actions_edit', 'action': 'edit', 'desc': 'edit actions'},
                  {'category': '/actions', 'plugin': 'actions_add', 'action': 'add', 'desc': 'add actions'},
                  {'category': '/users', 'plugin': 'users_list', 'action': 'list', 'desc': 'list users'},
                  {'category': '/users', 'plugin': 'users_del', 'action': 'del', 'desc': 'del users'},
                  {'category': '/users', 'plugin': 'users_edit', 'action': 'edit', 'desc': 'edit users'},
                  {'category': '/users', 'plugin': 'users_add', 'action': 'add', 'desc': 'add users'},
                  {'category': '/roles', 'plugin': 'roles_list', 'action': 'list', 'desc': 'list roles'},
                  {'category': '/roles', 'plugin': 'roles_del', 'action': 'del', 'desc': 'del roles'},
                  {'category': '/roles', 'plugin': 'roles_edit', 'action': 'edit', 'desc': 'edit roles'},
                  {'category': '/roles', 'plugin': 'roles_add', 'action': 'add', 'desc': 'add roles'},
                  {'category': '/secrets', 'plugin': 'secrets_list', 'action': 'list', 'desc': 'list secrets'},
                  {'category': '/secrets', 'plugin': 'secrets_del', 'action': 'del', 'desc': 'del secrets'},
                  {'category': '/secrets', 'plugin': 'secrets_edit', 'action': 'edit', 'desc': 'edit secrets'},
                  {'category': '/secrets', 'plugin': 'secrets_add', 'action': 'add', 'desc': 'add secrets'},
                  {'category': '/plugins', 'plugin': 'plugins_list', 'action': 'list', 'desc': 'list plugins'},
                  {'category': '/', 'plugin': 'ping', 'action': 'ping', 'desc': 'verify connectivity'},
                  {'category': '/', 'plugin': 'logs', 'action': 'logs', 'desc': 'show the history log'},
                  {'category': '/', 'plugin': 'help', 'action': 'help', 'desc': 'print usage'},
                  ]


def encrypt_dict(dictobj):
    # encrypt sensitive option vals
    for key in ["secret"]:
        if dictobj is not None and key in dictobj:
            dictobj[key] = encrypt_str(dictobj[key])


def decrypt_dict(dictobj):
    for key in ["secret"]:
        if dictobj is not None and key in dictobj:
            dictobj[key] = decrypt_str(dictobj[key])


def encrypt_str(text):
    global encryption_password
    if encryption_password is not None:
        encryption_suite = AES.new(encryption_password, AES.MODE_CFB, 'This is an IV456')
        return str(binascii.b2a_base64(encryption_suite.encrypt(text)))
    return str(text)


def decrypt_str(text):
    global encryption_password
    if encryption_password is not None:
        decryption_suite = AES.new(encryption_password, AES.MODE_CFB, 'This is an IV456')
        return str(decryption_suite.decrypt(binascii.a2b_base64(text)))
    return str(text)


def secret_has_permission(user, secret):
    cursor = db.roles.find()
    for doc in list(cursor):
        if user in list(doc["users"].split(",")):
            if "secrets" not in doc:
                # No secrets option, give them access to all secrets
                return True
            if secret in list(doc["secrets"].split(",")):
                return True
    return False


def roles_has_permission(user, action, options):
    # Ping is always allowed
    if action["category"] == "/" and action["action"] == "ping":
        return True
    # Help is always allowed
    if action["category"] == "/" and action["action"] == "help":
        return True

    if action["category"][-1:] == "/":
        action_str = "%s%s" % (action["category"], action["action"])
    else:
        action_str = "%s/%s" % (action["category"], action["action"])
    cursor = db.roles.find()
    for doc in list(cursor):
        if user in list(doc["users"].split(",")):
            for action in list(doc["actions"].split(",")):
                if re.match(r"^%s" % action, action_str):
                    return True
    return False


def render_secrets(user, dictobj):
    secrets = {}

    if dictobj is None or user is None:
        return None

    cursor = db.secrets.find()
    for doc in list(cursor):
        decrypt_dict(doc)
        if secret_has_permission(user, doc["name"]):
            secrets[doc["name"]] = doc["secret"]

    return render_vars("secret", secrets, dictobj)


def render_vars(varname, vardict, dictobj):
    if dictobj is None or vardict is None:
        return None

    for key in dictobj:
        if isinstance(dictobj[key], basestring):
            t = Template(dictobj[key])
            dictobj[key] = t.render({varname: vardict})

    return dictobj


def parse_action(user, category, action, options):
    cursor = db.actions.find()
    for dbaction in builtin_actions + list(cursor):
        if dbaction["category"] == category and dbaction["action"] == action:
            if "plugin" in dbaction:
                if not roles_has_permission(user, dbaction, options):
                    return json.dumps({"response": "  you do not have permission to run this action"})
                else:
                    # Admin functions do not allow secrets
                    if dbaction["category"] not in ["/actions", "/users", "/roles", "/secrets", "/plugins"]:
                        render_vars("option", options, dbaction)
                        render_secrets(user, dbaction)
                        render_secrets(user, options)
                    return plugins[dbaction["plugin"]](user, dbaction, options)
    return None


class Cli(object):
    """ outbit CLI """

    def __init__(self):
        """ Setup Arguments and Options for CLI """
        # Parse CLI Arguments
        parser = optparse.OptionParser()
        parser.add_option("-s", "--server", dest="server",
                          help="IP address or hostname of outbit-api server",
                          metavar="SERVER",
                          default=None)
        parser.add_option("-p", "--port", dest="port",
                          help="tcp port of outbit-api server",
                          metavar="PORT",
                          default=None)
        parser.add_option("-t", "--secure", dest="is_secure",
                          help="Use SSL",
                          metavar="SECURE",
                          action="store_true")
        parser.add_option("-d", "--debug", dest="is_debug",
                          help="Debug Mode",
                          metavar="DEBUG",
                          action="store_true")
        parser.add_option("-k", "--ssl_key", dest="ssl_key",
                          help="SSL key",
                          metavar="SSLKEY",
                          default=None)
        parser.add_option("-c", "--ssl_crt", dest="ssl_crt",
                          help="SSL certificate",
                          metavar="SSLCRT",
                          default=None)
        (options, args) = parser.parse_args()
        self.server = options.server
        self.port = options.port
        self.is_secure = options.is_secure
        self.is_debug = options.is_debug
        self.ssl_key = options.ssl_key
        self.ssl_crt = options.ssl_crt
        global encryption_password

        # Assign values from conf
        outbit_config_locations = [os.path.expanduser("~")+"/.outbit-api.conf", "/etc/outbit-api.conf"]
        outbit_conf_obj = {}
        for outbit_conf in outbit_config_locations:
            if os.path.isfile(outbit_conf):
                with open(outbit_conf, 'r') as stream:
                    try:
                        outbit_conf_obj = yaml.load(stream)
                    except yaml.YAMLError as excep:
                        print("%s\n" % excep)
        if self.server is None and "server" in outbit_conf_obj:
            self.server = str(outbit_conf_obj["server"])
        if self.port is None and "port" in outbit_conf_obj:
            self.port = int(outbit_conf_obj["port"])
        if self.is_secure == False and "secure" in outbit_conf_obj:
            self.is_secure = bool(outbit_conf_obj["secure"])
        if self.is_debug == False and "debug" in outbit_conf_obj:
            self.is_debug = bool(outbit_conf_obj["debug"])
        if encryption_password is None and "encryption_password" in outbit_conf_obj:
            encryption_password = str(outbit_conf_obj["encryption_password"])
        if self.ssl_key == None and "ssl_key" in outbit_conf_obj:
            self.ssl_key = bool(outbit_conf_obj["ssl_key"])
        if self.ssl_crt == None and "ssl_crt" in outbit_conf_obj:
            self.ssl_crt = bool(outbit_conf_obj["ssl_crt"])

        # Assign Default values if they were not specified at the cli or in the conf
        if self.server is None:
            self.server = "127.0.0.1"
        if self.port is None:
            self.port = 8088
        if self.ssl_key is None:
            self.ssl_key = "/usr/local/etc/openssl/certs/outbit.key"
        if self.ssl_crt is None:
            self.ssl_crt = "/usr/local/etc/openssl/certs/outbit.crt"

    def run(self):
        """ EntryPoint Of Application """

        # Setup logging to logfile (only if the file was touched)
        if os.path.isfile("/var/log/outbit.log"):
            handler = RotatingFileHandler('/var/log/outbit.log', maxBytes=10000, backupCount=1)
            handler.setLevel(logging.INFO)
            routes.app.logger.addHandler(handler)
            # Disable stdout logging since its logging to a log file
            log = logging.getLogger('werkzeug')
            log.disabled = True

        # First Time Defaults, Setup superadmin if it doesnt exist
        default_user = "superadmin"
        default_password = "superadmin"
        default_role = "super"
        # Create default user
        post = db.users.find_one({"username": default_user})
        if post is None:
            m = hashlib.md5()
            m.update(default_password)
            password_md5 = str(m.hexdigest())
            post = {"username": default_user, "password_md5": password_md5}
            db.users.insert_one(post)
        # Create default role
        post = db.roles.find_one({"name": default_role})
        if post is None:
            post = {"name": default_role, "users": default_user, "actions": "/"}
            db.roles.insert_one(post)

        # Start API Server
        routes.app.logger.info("Starting outbit api server on %s://%s:%d" % ("https" if
            self.is_secure else "http", self.server, self.port))
        if self.is_secure:
            context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            context.check_hostname = False
            context.load_cert_chain(certfile=self.ssl_crt, keyfile=self.ssl_key)
            routes.app.run(host=self.server, ssl_context=context, port=self.port, debug=self.is_debug)
        else:
            routes.app.run(host=self.server, port=self.port, debug=self.is_debug)



