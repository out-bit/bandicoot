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
    db = MongoClient('localhost').outbit

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
            "help": builtins.plugin_help,
            "ansible": builtins.plugin_ansible,
            "jobs_list": builtins.plugin_jobs_list,
            "jobs_status": builtins.plugin_jobs_status,
            "jobs_kill": builtins.plugin_jobs_kill,
            "schedules_list": builtins.plugin_schedules_list,
            "schedules_del": builtins.plugin_schedules_del,
            "schedules_edit": builtins.plugin_schedules_edit,
            "schedules_add": builtins.plugin_schedules_add,
            "inventory_list": builtins.plugin_inventory_list,
            "inventory_del": builtins.plugin_inventory_del,
           }

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
                  {'category': '/jobs', 'plugin': 'jobs_list', 'action': 'list', 'desc': 'list jobs'},
                  {'category': '/jobs', 'plugin': 'jobs_status', 'action': 'status', 'desc': 'get status of job'},
                  {'category': '/jobs', 'plugin': 'jobs_kill', 'action': 'kill', 'desc': 'kill a job'},
                  {'category': '/schedules', 'plugin': 'schedules_add', 'action': 'add', 'desc': 'add schedule'},
                  {'category': '/schedules', 'plugin': 'schedules_edit', 'action': 'edit', 'desc': 'edit schedule'},
                  {'category': '/schedules', 'plugin': 'schedules_list', 'action': 'list', 'desc': 'list schedules'},
                  {'category': '/schedules', 'plugin': 'schedules_del', 'action': 'del', 'desc': 'del schedule'},
                  {'category': '/inventory', 'plugin': 'inventory_list', 'action': 'list', 'desc': 'list inventory'},
                  {'category': '/inventory', 'plugin': 'inventory_del', 'action': 'del', 'desc': 'del inventory item'},
                  ]


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
    for key in ["secret"]:
        if dictobj is not None and key in dictobj:
            dictobj[key] = encrypt_str(dictobj[key])
    return True


def decrypt_dict(dictobj):
    for key in ["secret"]:
        if dictobj is not None and key in dictobj:
            decrypted_str = decrypt_str(dictobj[key])
            if decrypted_str is not None:
                dictobj[key] = decrypted_str
            else:
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


def encrypt_str(text, key_len=32):
    global encryption_password
    encryption_prefix = "__outbit_encrypted__:"
    encrypt_text = encryption_prefix + text
    if encryption_password is not None:
        salt = "__Salt__"
        key, iv = aes_derive_key_and_iv(encryption_password, salt, key_len, AES.block_size)
        encryption_suite = AES.new(key, AES.MODE_CFB, iv)
        return str(binascii.b2a_base64(encryption_suite.encrypt(encrypt_text)))
    return str(encrypt_text)


def decrypt_str(text, key_len=32):
    global encryption_password
    encryption_prefix = "__outbit_encrypted__:"
    if text[:len(encryption_prefix)] == encryption_prefix:
        # Clear Text, No Encryption Password Provided
        return str(text[len(encryption_prefix):])
    elif encryption_password is not None:
        # Decrypt using password
        salt = "__Salt__"
        key, iv = aes_derive_key_and_iv(encryption_password, salt, key_len, AES.block_size)
        decryption_suite = AES.new(key, AES.MODE_CFB, iv)
        decrypt_text = str(decryption_suite.decrypt(binascii.a2b_base64(text)))
        if decrypt_text[:len(encryption_prefix)] == encryption_prefix:
            # Clear Text, No Encryption Password Provided
            return str(decrypt_text[len(encryption_prefix):]) 
        else:
            # Decryption Failed, Probably Wrong Key
            return None
    else:
        # Decryption Failed, Its Not Clear Text
        return None


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
    if not os.path.isdir("/tmp/outbit/"):
        os.mkdir("/tmp/outbit")

    # Make sure directory permissions are secure
    os.chmod("/tmp/outbit/", 0700)

    for filename in glob("/tmp/outbit/*"):
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
    filepath = "/tmp/outbit/"
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
        if dbaction["category"] == category and dbaction["action"] == action:
            if "plugin" in dbaction:
                if not roles_has_permission(user, dbaction, options):
                    return json.dumps({"response": "  you do not have permission to run this action"})
                else:
                    # Admin functions do not allow secrets
                    if (dbaction["category"] not in ["/actions", "/users", "/roles", "/secrets", "/plugins"]) and dbaction["category"] == "/" and dbaction["action"] not in ["ping"]:
                            render_vars("option", options, dbaction)
                            tmp_files_dbaction = render_secrets(user, dbaction)
                            tmp_files_options = render_secrets(user, options)

                            # Check Decryption Worked
                            if user is not None:
                                if (dbaction is not None and tmp_files_dbaction is None) or (options is not None and tmp_files_options is None):
                                    return json.dumps({"response": "  error: Failed to decrypt a secret. If you recently changed your encryption_password try 'secrets change_encryptpw oldpw=XXXX newpw=XXXX'."})

                            response = plugins[dbaction["plugin"]](user, dbaction, options)
                            response = json.loads(response)
                            clean_secrets(tmp_files_dbaction)
                            clean_secrets(tmp_files_options)

                            # async, return queue_id
                            if "response" not in response:
                                if "queue_id" not in response:
                                    return json.dumps({"response": "  error: expected async queue id but found none"})

                            return json.dumps(response)
                    else:
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
        if ldap_server == None and "ldap_server" in outbit_conf_obj:
            ldap_server = options.ldap_server
        if ldap_use_ssl == None and "ldap_use_ssl" in outbit_conf_obj:
            ldap_use_ssl = options.ldap_use_ssl
        if ldap_user_cn == None and "ldap_user_cn" in outbit_conf_obj:
            ldap_user_cn = options.ldap_user_cn

        # Assign Default values if they were not specified at the cli or in the conf
        if self.server is None:
            self.server = "127.0.0.1"
        if self.port is None:
            self.port = 8088
        if self.ssl_key is None:
            self.ssl_key = "/usr/local/etc/openssl/certs/outbit.key"
        if self.ssl_crt is None:
            self.ssl_crt = "/usr/local/etc/openssl/certs/outbit.crt"
        if ldap_server is None:
            ldap_server = options.ldap_server
        if ldap_use_ssl is None:
            ldap_use_ssl = options.ldap_use_ssl
        if ldap_user_cn is None:
            ldap_user_cn = options.ldap_user_cn

        # Clean any left over secret files
        clean_all_secrets()

    def run(self):
        """ EntryPoint Of Application """
        global db

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

        # Start Scheduler
        p = multiprocessing.Process(target=schedule_manager)
        p.start()

        # Setup DB Connection
        db = MongoClient('localhost').outbit

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
        routes.app.logger.info("Starting outbit api server on %s://%s:%d" % ("https" if
            self.is_secure else "http", self.server, self.port))
        if self.is_secure:
            context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            context.check_hostname = False
            context.load_cert_chain(certfile=self.ssl_crt, keyfile=self.ssl_key)
            routes.app.run(host=self.server, ssl_context=context, port=self.port, debug=self.is_debug)
        else:
            routes.app.run(host=self.server, port=self.port, debug=self.is_debug)



