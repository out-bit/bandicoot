""" Command Line Interface Module """
import optparse
import sys
import os
import yaml
import re
import json
import hashlib
from pymongo import MongoClient
from bandicoot.restapi import routes
from bandicoot.plugins import builtins
from bandicoot.exceptions import DecryptWrongKeyException, DecryptNotClearTextException, DecryptException
from Crypto.Cipher import AES
from hashlib import md5
import binascii
from jinja2 import Template
import ssl
import logging
from logging.handlers import RotatingFileHandler
import time
from glob import glob
import shutil
import datetime
import multiprocessing
import copy


db = None
encryption_password = None
ldap_server = None
ldap_use_ssl = True
ldap_user_cn = None


def counters_db_init(name):
    result = db.counters.find_one( {"_id": name} )
    if result is None:
        db.counters.insert_one( {"_id": name, "seq": 0 } )


def counters_db_getNextSequence(name):
   ret = db.counters.update_one({ "_id": name },
                                { "$inc": { "seq": 1 } },
                                )
   result = db.counters.find_one( {"_id": name} )
   return result["seq"]


def schedule_manager():
    schedule_last_run = {} # stores last run times for 
    global db

    # Setup DB Connection For Thread
    db = MongoClient('localhost').bandicoot

    while True:
        # Get Current Time
        cron_minute = datetime.datetime.now().minute
        cron_hour = datetime.datetime.now().hour
        cron_day_of_month = datetime.datetime.today().day
        cron_month = datetime.datetime.today().month
        cron_day_of_week = datetime.datetime.today().weekday()

        cursor = db.schedules.find()
        for doc in list(cursor):
            name = doc["name"]
            user = doc["user"]
            category = doc["category"]
            action = doc["action"]
            options = None # Default (NOT WORKING)
            minute = "*" # Default
            hour = "*" # Default
            day_of_month = "*" # Default
            month = "*" # Default
            day_of_week = "*" # Default

            if "options" in doc:
                options = doc["options"]
            if "minute" in doc:
                minute = doc["minute"]
            if "hour" in doc:
                hour = doc["hour"]
            if "day_of_month" in doc:
                day_of_month = doc["day_of_month"]
            if "month" in doc:
                month = doc["month"]
            if "day_of_week" in doc:
                day_of_week = doc["day_of_week"]

            # * matches anything, so make it match the current time
            if minute == "*":
                minute = cron_minute
            else:
                minute = int(minute)

            if hour == "*":
                hour = cron_hour
            else:
                hour = int(hour)

            if day_of_month == "*":
                day_of_month = cron_day_of_month
            else:
                day_of_month = int(day_of_month)

            if month == "*":
                month = cron_month
            else:
                month = int(month)

            if day_of_week == "*":
                day_of_week = cron_day_of_week
            else:
                day_of_week = int(day_of_week)

            # Check if cron should be run, see if each setting matches
            # If name is not in schedule_last_run its the first time running it, so thats ok.
            # If name is already in schedule_last_run then check to make sure it didnt already run within the same minute
            if cron_minute == minute and \
               cron_hour == hour and \
               cron_day_of_month == day_of_month and \
               cron_month == month and \
               cron_day_of_week == day_of_week and \
               (name not in schedule_last_run or \
               not (schedule_last_run[name][0] == cron_minute and \
               schedule_last_run[name][1] == cron_hour and \
               schedule_last_run[name][2] == cron_day_of_month and \
               schedule_last_run[name][3] == cron_month and \
               schedule_last_run[name][4] == cron_day_of_week)):

                # Run Scheduled Action
                dat = parse_action(user, category, action, options)

                # Audit Logging / History
                log_action(user, {"result": dat, "category": category, "action": action, "options": options})

                schedule_last_run[name] = (cron_minute, cron_hour, cron_day_of_month, cron_month, cron_day_of_week)

        # Delay 10 seconds between each check
        time.sleep(10)


plugins = {}

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
                  {'category': '/secrets', 'plugin': 'secrets_encryptpw', 'action': 'encryptpw', 'desc': 'Change password encryption'},
                  {'category': '/plugins', 'plugin': 'plugins_list', 'action': 'list', 'desc': 'list plugins'},
                  {'category': '/', 'plugin': 'ping', 'action': 'ping', 'desc': 'verify connectivity'},
                  {'category': '/', 'plugin': 'logs', 'action': 'logs', 'desc': 'show the history log'},
                  {'category': '/', 'plugin': 'help', 'action': 'help', 'desc': 'print usage'},
                  {'category': '/help', 'plugin': 'help', 'action': '*', 'desc': 'print usage'},
                  {'category': '/jobs', 'plugin': 'jobs_list', 'action': 'list', 'desc': 'list jobs'},
                  {'category': '/jobs', 'plugin': 'jobs_status', 'action': 'status', 'desc': 'get status of job'},
                  {'category': '/jobs', 'plugin': 'jobs_kill', 'action': 'kill', 'desc': 'kill a job'},
                  {'category': '/schedules', 'plugin': 'schedules_add', 'action': 'add', 'desc': 'add schedule'},
                  {'category': '/schedules', 'plugin': 'schedules_edit', 'action': 'edit', 'desc': 'edit schedule'},
                  {'category': '/schedules', 'plugin': 'schedules_list', 'action': 'list', 'desc': 'list schedules'},
                  {'category': '/schedules', 'plugin': 'schedules_del', 'action': 'del', 'desc': 'del schedule'},
                  {'category': '/inventory', 'plugin': 'inventory_list', 'action': 'list', 'desc': 'list inventory'},
                  {'category': '/inventory', 'plugin': 'inventory_del', 'action': 'del', 'desc': 'del inventory item'},
                  {'category': '/', 'plugin': 'stats', 'action': 'stats', 'desc': 'statistics'},
                  ]


def load_plugins(plugin_paths=None):
    default_plugin_path = os.path.dirname(os.path.realpath(__file__)) + "/../plugins/"
    if plugin_paths is None:
        plugin_paths = default_plugin_path
    for plugin_path in plugin_paths.split(":"):
        sys.path.append(plugin_path)
        for file in os.listdir(plugin_path):
            if file.endswith(".py") and file != "__init__.py":
                plugin_module = __import__(file.rstrip(".py"), fromlist=[''])
                load_plugins_from_module(plugin_module)


def load_plugins_from_module(module):
    import inspect
    global plugins
    for member in inspect.getmembers(module):
        plugin_name = member[0]
        plugin_function = member[1]
        if inspect.isfunction(plugin_function):
            if plugin_name not in plugins:
                m = re.match(r'^plugin_(.*?)$', plugin_name)
                if m:
                    plugin_short_name = m.group(1)
                    plugins[plugin_short_name] = plugin_function


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
        db.logs.insert_one(post)


def encrypt_dict(dictobj):
    # encrypt sensitive option vals
    global encryption_password
    for key in ["secret"]:
        if dictobj is not None and key in dictobj:
            dictobj[key] = encrypt_str(dictobj[key], encryption_password)
    return True


def decrypt_dict(dictobj):
    # decrypt sensitive option vals
    global encryption_password
    for key in ["secret"]:
        if dictobj is not None and key in dictobj:
            try:
                decrypted_str = decrypt_str(dictobj[key], encryption_password, keyname=dictobj["name"])
                dictobj[key] = decrypted_str
            except DecryptException:
                return False
    return True


def aes_derive_key_and_iv(password, salt, key_length, iv_length):
    """ source: Ansible source code """
    """ Create a key and an initialization vector """
    d = d_i = ''
    while len(d) < key_length + iv_length:
        text = ''.join([d_i, password, salt])
        d_i = str(md5(text).digest())
        d += d_i
    key = d[:key_length]
    iv = d[key_length:key_length+iv_length]
    return key, iv


def encrypt_str(text, encrypt_password=None, key_len=32, encryption_prefix="__bandicoot_encrypted__:"):
    global encryption_password
    if encrypt_password is None and encryption_password is not None:
        # If No encryption password provided, use global encryption password
        encrypt_password = encryption_password
    encrypt_text = encryption_prefix + text
    if encrypt_password is not None:
        salt = "__Salt__"
        key, iv = aes_derive_key_and_iv(encrypt_password, salt, key_len, AES.block_size)
        encryption_suite = AES.new(key, AES.MODE_CFB, iv)
        return str(binascii.b2a_base64(encryption_suite.encrypt(encrypt_text)))
    return str(encrypt_text)


def decrypt_str(text, encrypt_password=None, key_len=32, encryption_prefix="__bandicoot_encrypted__:", keyname="unknown"):
    global encryption_password
    if encrypt_password is None and encryption_password is not None:
        # If No encryption password provided, use global encryption password
        encrypt_password = encryption_password
    if text[:len(encryption_prefix)] == encryption_prefix:
        # Clear Text, No Encryption Password Provided
        return str(text[len(encryption_prefix):])
    elif encrypt_password is not None:
        # Decrypt using password
        salt = "__Salt__"
        key, iv = aes_derive_key_and_iv(encrypt_password, salt, key_len, AES.block_size)
        decryption_suite = AES.new(key, AES.MODE_CFB, iv)
        decrypt_text = str(decryption_suite.decrypt(binascii.a2b_base64(text)))
        if decrypt_text[:len(encryption_prefix)] == encryption_prefix:
            # Decrypted Text
            return str(decrypt_text[len(encryption_prefix):]) 
        else:
            # Probably Wrong Key
            raise DecryptWrongKeyException("  error: Failed to decrypt a secret named %s. If you recently changed your encryption_password try 'secrets encryptpw oldpw=XXXX newpw=XXXX'." % keyname)
    else:
        # Decryption Failed, Its Not Clear Text
        raise DecryptNotClearTextException("  error: Failed to decrypt a secret named %s. If you recently disabled your encryption_password then re-enable it." % keyname)


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
    # jobs status is always allowed
    if action["category"] == "/jobs" and action["action"] == "status":
        return True
    # jobs list is always allowed
    if action["category"] == "/jobs" and action["action"] == "list":
        return True
    # jobs kill is always allowed
    if action["category"] == "/jobs" and action["action"] == "kill":
        return True
    """ This allows users to edit their own password.
     sers edit password is allowed if the username is only changing their own password.
     If username is not in options, that means their changing their own password. """
    if action["category"] == "/users" and action["action"] == "edit" and ("username" not in options or options["username"] == user):
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


def clean_all_secrets():
    if not os.path.isdir("/tmp/bandicoot/"):
        os.mkdir("/tmp/bandicoot")

    # Make sure directory permissions are secure
    os.chmod("/tmp/bandicoot/", 0700)

    for filename in glob("/tmp/bandicoot/*"):
        if os.path.isdir(filename):
            shutil.rmtree(filename)
        else:
            os.remove(filename)


def clean_secrets(secrets):
    if secrets is None:
        return None

    for filename in secrets:
        # Temp File must exist
        if os.path.isfile(filename):
            # Delete secret files
            os.remove(filename)


def render_secret_file(name, secret):
    filepath = "/tmp/bandicoot/"
    filename = "%s.%s" % (name, time.time())
    fullpath = "%s%s" % (filepath, filename)

    if not os.path.isdir(filepath):
        os.mkdir(filepath)

    with open(fullpath, "w") as textfile:
        textfile.write(secret)

    os.chmod(fullpath, 0700)

    return fullpath


def render_secrets(user, dictobj):
    secrets = {}
    tmp_secret_files = []

    if dictobj is None or user is None:
        return None

    cursor = db.secrets.find()
    for doc in list(cursor):
        res = decrypt_dict(doc)
        if res is False:
            # Decryption Failed
            return None
        if secret_has_permission(user, doc["name"]):
            if "type" in doc and doc["type"] == "file":
                secrets[doc["name"]] = render_secret_file(doc["name"], doc["secret"])
                tmp_secret_files.append(secrets[doc["name"]])
            else:
                secrets[doc["name"]] = doc["secret"]

    render_vars("secret", secrets, dictobj)
    return tmp_secret_files


def render_vars(varname, vardict, dictobj):
    if dictobj is None or vardict is None:
        return None

    for key in dictobj:
        if isinstance(dictobj[key], basestring):
            t = Template(dictobj[key])
            dictobj[key] = t.render({varname: vardict})


def parse_action(user, category, action, options):
    cursor = db.actions.find()
    for dbaction in builtin_actions + list(cursor):
        if dbaction["category"] == category and (dbaction["action"] == action or dbaction["action"] == "*"):
            new_dbaction = copy.copy(dbaction) # Make a copy to prevent modifying global builtin_actions
            new_dbaction["action"] = action
            if "plugin" in dbaction:
                if not roles_has_permission(user, dbaction, options):
                    return json.dumps({"response": "  you do not have permission to run this action"})
                else:
                    # Admin functions do not allow secrets
                    if dbaction["category"] not in ["/actions", "/users", "/roles", "/secrets", "/plugins"]:
                        if dbaction["category"] == "/" and dbaction["action"] in ["ping"]:
                            # /ping does not allow secrets
                            pass
                        else:
                            # Run Plugin With Secret
                            render_vars("option", options, dbaction)
                            tmp_files_dbaction = render_secrets(user, dbaction)
                            tmp_files_options = render_secrets(user, options)

                            # Check Decryption Failed
                            if user is not None:
                                if (dbaction is not None and tmp_files_dbaction is None) or (options is not None and tmp_files_options is None):
                                    return json.dumps({"response": "  error: Failed to decrypt a secret. If you recently changed your encryption_password try 'secrets encryptpw oldpw=XXXX newpw=XXXX'."})

                            response = plugins[dbaction["plugin"]](user, new_dbaction, options)
                            response = json.loads(response)
                            clean_secrets(tmp_files_dbaction)
                            clean_secrets(tmp_files_options)

                            # async, return queue_id
                            if "response" not in response:
                                if "queue_id" not in response:
                                    return json.dumps({"response": "  error: expected async queue id but found none"})

                            return json.dumps(response)
                    # Run Plugin Without Secrets
                    return plugins[dbaction["plugin"]](user, new_dbaction, options)
    return None


class Cli(object):
    """ bandicoot CLI """

    def __init__(self):
        """ Setup Arguments and Options for CLI """
        # Parse CLI Arguments
        parser = optparse.OptionParser()
        parser.add_option("-s", "--server", dest="server",
                          help="IP address or hostname of bandicoot-api server",
                          metavar="SERVER",
                          default=None)
        parser.add_option("-p", "--port", dest="port",
                          help="tcp port of bandicoot-api server",
                          metavar="PORT",
                          default=None)
        parser.add_option("-t", "--insecure", dest="is_secure",
                          help="Do Not Use SSL",
                          metavar="SECURE",
                          action="store_false",
                          default=True)
        parser.add_option("-d", "--debug", dest="is_debug",
                          help="Debug Mode",
                          metavar="DEBUG",
                          action="store_true",
                          default=False)
        parser.add_option("-k", "--ssl_key", dest="ssl_key",
                          help="SSL key",
                          metavar="SSLKEY",
                          default=None)
        parser.add_option("-c", "--ssl_crt", dest="ssl_crt",
                          help="SSL certificate",
                          metavar="SSLCRT",
                          default=None)
        parser.add_option("-l", "--ldap_server", dest="ldap_server",
                          help="LDAP Server for Authentiation",
                          metavar="LDAPSERVER",
                          default=None)
        parser.add_option("-z", "--ldap_use_ssl", dest="ldap_use_ssl",
                          help="Enable SSL for LDAP",
                          metavar="LDAPUSESSL",
                          default=None)
        parser.add_option("-x", "--ldap_user_cn", dest="ldap_user_cn",
                          help="LDAP User CN",
                          metavar="LDAPUSERCN",
                          default=None)
        parser.add_option("-P", "--pluginpath", dest="pluginpath",
                          help="Plugin Paths, seperated by :",
                          metavar="PLUGINPATH",
                          default=None)
        global encryption_password
        global ldap_server
        global ldap_use_ssl
        global ldap_user_cn
        (options, args) = parser.parse_args()
        self.server = options.server
        self.port = options.port
        self.is_secure = options.is_secure
        self.is_debug = options.is_debug
        self.ssl_key = options.ssl_key
        self.ssl_crt = options.ssl_crt
        ldap_server = options.ldap_server
        ldap_use_ssl = options.ldap_use_ssl
        ldap_user_cn = options.ldap_user_cn
        pluginpath = options.pluginpath

        # Assign values from conf
        bandicoot_config_locations = [os.path.expanduser("~")+"/.bandicoot-api.conf", "/etc/bandicoot-api.conf"]
        bandicoot_conf_obj = {}
        for bandicoot_conf in bandicoot_config_locations:
            if os.path.isfile(bandicoot_conf):
                with open(bandicoot_conf, 'r') as stream:
                    try:
                        bandicoot_conf_obj = yaml.load(stream)
                    except yaml.YAMLError as excep:
                        print("%s\n" % excep)
        if self.server is None and "server" in bandicoot_conf_obj:
            self.server = str(bandicoot_conf_obj["server"])
        if self.port is None and "port" in bandicoot_conf_obj:
            self.port = int(bandicoot_conf_obj["port"])
        if self.is_secure == True and "secure" in bandicoot_conf_obj:
            self.is_secure = bool(bandicoot_conf_obj["secure"])
        if self.is_debug == True and "debug" in bandicoot_conf_obj:
            self.is_debug = bool(bandicoot_conf_obj["debug"])
        if encryption_password is None and "encryption_password" in bandicoot_conf_obj:
            encryption_password = str(bandicoot_conf_obj["encryption_password"])
        if self.ssl_key == None and "ssl_key" in bandicoot_conf_obj:
            self.ssl_key = bool(bandicoot_conf_obj["ssl_key"])
        if self.ssl_crt == None and "ssl_crt" in bandicoot_conf_obj:
            self.ssl_crt = bool(bandicoot_conf_obj["ssl_crt"])
        if ldap_server == None and "ldap_server" in bandicoot_conf_obj:
            ldap_server = str(bandicoot_conf_obj["ldap_server"])
        if ldap_use_ssl == None and "ldap_use_ssl" in bandicoot_conf_obj:
            ldap_use_ssl = str(bandicoot_conf_obj["ldap_use_ssl"])
        if ldap_user_cn == None and "ldap_user_cn" in bandicoot_conf_obj:
            ldap_user_cn = str(bandicoot_conf_obj["ldap_user_cn"])
        if pluginpath == None and "pluginpath" in bandicoot_conf_obj:
            pluginpath = str(bandicoot_conf_obj["pluginpath"])

        # Assign Default values if they were not specified at the cli or in the conf
        if self.server is None:
            self.server = "127.0.0.1"
        if self.port is None:
            self.port = 8088
        if self.ssl_key is None:
            self.ssl_key = "/usr/local/etc/openssl/certs/bandicoot.key"
        if self.ssl_crt is None:
            self.ssl_crt = "/usr/local/etc/openssl/certs/bandicoot.crt"
        if ldap_server is None:
            ldap_server = options.ldap_server
        if ldap_use_ssl is None:
            ldap_use_ssl = options.ldap_use_ssl
        if ldap_user_cn is None:
            ldap_user_cn = options.ldap_user_cn

        # Load Plugins
        load_plugins(pluginpath)

        # Clean any left over secret files
        clean_all_secrets()

    def run(self):
        """ EntryPoint Of Application """
        global db

        # Setup logging to logfile (only if the file was touched)
        if os.path.isfile("/var/log/bandicoot.log"):
            handler = RotatingFileHandler('/var/log/bandicoot.log', maxBytes=10000, backupCount=1)

        # Assign Default values if they were not specified at the cli or in the conf
        if self.server is None:
            self.server = "127.0.0.1"
        if self.port is None:
            self.port = 8088
        if self.ssl_key is None:
            self.ssl_key = "/usr/local/etc/openssl/certs/bandicoot.key"
        if self.ssl_crt is None:
            self.ssl_crt = "/usr/local/etc/openssl/certs/bandicoot.crt"
        if ldap_server is None:
            ldap_server = options.ldap_server
        if ldap_use_ssl is None:
            ldap_use_ssl = options.ldap_use_ssl
        if ldap_user_cn is None:
            ldap_user_cn = options.ldap_user_cn

        # Load Plugins
        load_plugins(pluginpath)

        # Clean any left over secret files
        clean_all_secrets()

    def run(self):
        """ EntryPoint Of Application """
        global db

        # Setup logging to logfile (only if the file was touched)
        if os.path.isfile("/var/log/bandicoot.log"):
            handler = RotatingFileHandler('/var/log/bandicoot.log', maxBytes=10000, backupCount=1)
            handler.setLevel(logging.INFO)
            routes.app.logger.addHandler(handler)
            # Disable stdout logging since its logging to a log file
            log = logging.getLogger('werkzeug')
            log.disabled = True

        # First Time Defaults, Setup superadmin if it doesnt exist
        default_user = "superadmin"
        default_password = "superadmin"
        default_role = "super"

        # Start Scheduler
        p = multiprocessing.Process(target=schedule_manager)
        p.start()

        # Setup DB Connection
        db = MongoClient('localhost').bandicoot

        # Init db counters for jobs
        counters_db_init("jobid")

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
        routes.app.logger.info("Starting bandicoot api server on %s://%s:%d" % ("https" if
            self.is_secure else "http", self.server, self.port))
        if self.is_secure:
            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
            context.check_hostname = False
            context.load_cert_chain(certfile=self.ssl_crt, keyfile=self.ssl_key)
            routes.app.run(threaded=True, host=self.server, ssl_context=context, port=self.port, debug=self.is_debug)
        else:
            routes.app.run(threaded=True, host=self.server, port=self.port, debug=self.is_debug)



