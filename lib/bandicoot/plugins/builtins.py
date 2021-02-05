import bandicoot.cli.api
from bandicoot.exceptions import DecryptWrongKeyException, DecryptNotClearTextException, DecryptException
import json
import subprocess
import hashlib
import datetime
import re
import shutil
import time
import multiprocessing
import threading
import sys
import Queue
import os


job_queue = {}
EOF = -1


def queue_support():
    def wrap(f):
        def wrapped_f(*args):
            global job_queue
            user = args[0]
            action = args[1]
            options = args[2]
            exit_event = multiprocessing.Event()
            q = multiprocessing.Queue()
            p = multiprocessing.Process(target=f, args=args+(exit_event,q))
            job_id = int(bandicoot.cli.api.counters_db_getNextSequence("jobid"))
            bandicoot.cli.api.db.jobs.insert_one({"_id": int(job_id), "start_time": time.time(), "user": user, "action": action, "options": options, "running": True, "response": ""})
            job_queue[job_id] = { "queue": q, "process": p, "exit_event": exit_event}
            p.start()
            return json.dumps({"queue_id": job_id})
        wrapped_f._original = f
        return wrapped_f
    return wrap


def options_validator(option_list, regexp):
    def wrap(f):
        def wrapped_f(*args):
            user = args[0]
            action = args[1]
            options = args[2]
            if options is not None:
                for key in options:
                    if key in option_list and not re.match(regexp, options[key]):
                        return json.dumps({"exit_code": 1, "response": "  option %s=%s has invalid characters" % (key, options[key])})
            return f(*args)
        return wrapped_f
    return wrap


def options_required(option_list):
    def wrap(f):
        def wrapped_f(*args):
            user = args[0]
            action = args[1]
            options = args[2]
            if options is not None:
                # Loop through required options
                for key in option_list:
                    # Check if each required option was given by the users options
                    if key not in options:
                        return json.dumps({"exit_code": 1, "response": "  %s option is required" % key})
            return f(*args)
        return wrapped_f
    return wrap


def options_supported(option_list):
    def wrap(f):
        def wrapped_f(*args):
            user = args[0]
            action = args[1]
            options = args[2]
            if options is not None:
                # Loop through supported options
                for key in options:
                    # Check if unsupported option was provided
                    if key not in option_list:
                        return json.dumps({"exit_code": 1, "response": "  %s option is not supported. Supported options are: %s." % (key, ", ".join(option_list))})
            return f(*args)
        return wrapped_f
    return wrap


def category_fix(options):
    if "category" in options:
        if options["category"] != "/":
            options["category"] = options["category"].rstrip("/")
            if len(options["category"]) >= 1:
                if options["category"][0] != "/":
                    options["category"] = "/" + options["category"]


def plugin_help(user, action, options):
    cursor = bandicoot.cli.api.db.actions.find()
    response = ""
    api_response = []
    compact_actions = {}
    dbaction_count = 0

    # Build Compact, Sortable, Dictinary like: {"roles": {"actions": ["list", "edit"], "num": 0}}
    for dbaction in bandicoot.cli.api.builtin_actions + list(cursor):
        if not bandicoot.cli.api.roles_has_permission(user, {"category": dbaction["category"], "action": dbaction["action"]}, {}):
            continue

        if dbaction["category"] not in compact_actions:
            compact_actions[dbaction["category"]] = {"actions" : [dbaction["action"]], "descs": [dbaction["desc"]]}
            compact_actions[dbaction["category"]]["num"] = dbaction_count
        else:
            compact_actions[dbaction["category"]]["actions"].append(dbaction["action"])
            compact_actions[dbaction["category"]]["descs"].append(dbaction["desc"])
            compact_actions[dbaction["category"]]["num"] = dbaction_count
        dbaction_count += 1

    # Print Compact Help for the top level
    for db_item in sorted(compact_actions.items(), key=lambda x: x[1]['num']):
        dbaction["category"] = db_item[0]
        dbaction["actions"] = db_item[1]["actions"]
        dbaction["descs"] = db_item[1]["descs"]
        # Help specifying command
        if action["category"] == "/help":
            a_count = 0
            for actionline in dbaction["actions"]:
                if dbaction["category"].strip("/") == action["action"].strip("/"):
                    response += "  %s\t%s\n" % (actionline, dbaction["descs"][a_count])
                    a_count += 1
            api_response.append({"category": "", "action": dbaction["actions"], "desc": dbaction["descs"]})
        # Help by itself, no command
        else:
            category_str = dbaction['category'].strip("/").replace("/", " ")
            if category_str is None or len(category_str) <= 0:
                api_response.append({"category": "", "action": dbaction["actions"], "desc": dbaction["descs"]})
                for actionline in dbaction["actions"]:
                    response += "  %s\n" % actionline
            else:
                api_response.append({"category": dbaction["category"].strip("/").replace("/", " "), "action": dbaction["actions"], "desc": dbaction["descs"]})
                response += "  %s [%s]\n" % (dbaction["category"].strip("/").replace("/", " "), "|".join(dbaction["actions"]))

    # Append the exit builtin implemented on the client side
    response += "  exit \t\t\n"

    return json.dumps({"exit_code": 0, "response": response, "api_response": api_response})


def plugin_ping(user, action, options):
    return json.dumps({"exit_code": 0, "response": "  pong"})


@options_supported(option_list=["username", "password"])
@options_required(option_list=["username", "password"])
@options_validator(option_list=["username"], regexp=r'^[a-zA-Z0-9_\-]+$')
def plugin_users_add(user, action, options):
    result = bandicoot.cli.api.db.users.find_one({"username": options["username"]})
    if result is None:
        m = hashlib.md5()
        m.update(str(options["password"]))
        password_md5 = str(m.hexdigest())
        post = {"username": options["username"], "password_md5": password_md5}
        bandicoot.cli.api.db.users.insert_one(post)
        return json.dumps({"exit_code": 0, "response": "  created user %s" % options["username"]})
    else:
        return json.dumps({"exit_code": 1, "response": "  user %s already exists" % options["username"]})


@options_supported(option_list=["username"])
@options_required(option_list=["username"])
@options_validator(option_list=["username"], regexp=r'^[a-zA-Z0-9_\-]+$')
def plugin_users_del(user, action, options):
    post = {"username": options["username"]}
    result = bandicoot.cli.api.db.users.delete_many(post)
    if result.deleted_count > 0:
        return json.dumps({"exit_code": 0, "response": "  deleted user %s" % options["username"]})
    else:
        return json.dumps({"exit_code": 1, "response": "  user %s does not exist" % options["username"]})


@options_supported(option_list=["username", "password"])
@options_required(option_list=["password"])
@options_validator(option_list=["username"], regexp=r'^[a-zA-Z0-9_\-]+$')
def plugin_users_edit(user, action, options):
    # Hash the password
    m = hashlib.md5()
    m.update(options["password"])
    password_md5 = str(m.hexdigest())

    # If no username was specified, by default edit the current user
    if "username" not in options:
        options["username"] = user

    result = bandicoot.cli.api.db.users.update_one({"username": options["username"]},
            {"$set": {"password_md5": password_md5},})
    if result.matched_count > 0:
        return json.dumps({"exit_code": 0, "response": "  modified user %s" % options["username"]})
    else:
        return json.dumps({"exit_code": 1, "response": "  user %s does not exist" % options["username"]})


def plugin_users_list(user, action, options):
    result = ""
    cursor = bandicoot.cli.api.db.users.find()
    for doc in list(cursor):
        result += "  %s\n" % doc["username"]
    return json.dumps({"exit_code": 0, "response": result.rstrip()}) # Do not return the last character (carrage return)


@options_required(option_list=["name", "category", "action", "plugin", "desc"])
@options_validator(option_list=["name", "plugin", "action"], regexp=r'^[a-zA-Z0-9_\-]+$')
@options_validator(option_list=["category"], regexp=r'^[a-zA-Z0-9_\-/]+$')
def plugin_actions_add(user, action, options):
    dat = None

    category_fix(options)

    find_result = bandicoot.cli.api.db.actions.find_one({"name": options["name"]})
    if find_result is None:
        result = bandicoot.cli.api.db.actions.insert_one(options)
        dat = json.dumps({"exit_code": 0, "response": "  created action %s" % options["name"]})
    else:
        dat = json.dumps({"exit_code": 1, "response": "  action %s already exists" % options["name"]})
    return dat


def plugin_command(user, action, options):
    result = ""
    if "command_run" not in action:
        return json.dumps({"exit_code": 1, "response": "  command_run required in action"})
    cmd = action["command_run"].split()
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    for line in p.stdout:
        result += "  %s\n" % line
    p.wait()
    result += "  return code: %d\n"  % p.returncode
    return json.dumps({ "exit_code": 0, "response": result})


@options_required(option_list=["name"])
@options_validator(option_list=["name", "plugin", "action"], regexp=r'^[a-zA-Z0-9_\-]+$')
@options_validator(option_list=["category"], regexp=r'^[a-zA-Z0-9_\-/]+$')
def plugin_actions_edit(user, action, options):
    category_fix(options)

    result = bandicoot.cli.api.db.actions.update_one({"name": options["name"]},
            {"$set": options})
    if result.matched_count > 0:
        return json.dumps({"exit_code": 0, "response": "  modified action %s" % options["name"]})
    else:
        return json.dumps({"exit_code": 1, "response": "  action %s does not exist" % options["name"]})


@options_supported(option_list=["name"])
@options_required(option_list=["name"])
@options_validator(option_list=["name"], regexp=r'^[a-zA-Z0-9_\-]+$')
def plugin_actions_del(user, action, options):
    dat = None

    post = {"name": options["name"]}
    result = bandicoot.cli.api.db.actions.delete_many(post)
    if result.deleted_count > 0:
        dat = json.dumps({"exit_code": 0, "response": "  deleted action %s" % options["name"]})
    else:
        dat = json.dumps({"exit_code": 1, "response": "  action %s does not exist" % options["name"]})
    return dat


def plugin_actions_list(user, action, options):
    result = ""
    cursor = bandicoot.cli.api.db.actions.find()
    for doc in list(cursor):
        for key in sorted(doc):
            if key not in ["_id"]:
                result += '  %s="%s" ' % (key, doc[key])
        result += "\n"
    return json.dumps({"exit_code": 0, "response": result.rstrip()}) # Do not return the last character (carrage return)


@options_required(option_list=["name"])
@options_validator(option_list=["name"], regexp=r'^[a-zA-Z0-9_\-]+$')
def plugin_roles_add(user, action, options):
    result = bandicoot.cli.api.db.roles.find_one({"name": options["name"]})
    if result is None:
        post = options
        bandicoot.cli.api.db.roles.insert_one(post)
        return json.dumps({"exit_code": 0, "response": "  created role %s" % options["name"]})
    else:
        return json.dumps({"exit_code": 1, "response": "  role %s already exists" % options["name"]})


@options_required(option_list=["name"])
@options_validator(option_list=["name"], regexp=r'^[a-zA-Z0-9_\-]+$')
def plugin_roles_edit(user, action, options):
    result = bandicoot.cli.api.db.roles.update_one({"name": options["name"]},
            {"$set": options})
    if result.matched_count > 0:
        return json.dumps({"exit_code": 0, "response": "  modified role %s" % options["name"]})
    else:
        return json.dumps({"exit_code": 1, "response": "  role %s does not exist" % options["name"]})


@options_supported(option_list=["name"])
@options_required(option_list=["name"])
@options_validator(option_list=["name"], regexp=r'^[a-zA-Z0-9_\-]+$')
def plugin_roles_del(user, action, options):
    post = {"name": options["name"]}
    result = bandicoot.cli.api.db.roles.delete_many(post)
    if result.deleted_count > 0:
        return json.dumps({"exit_code": 0, "response": "  deleted role %s" % options["name"]})
    else:
        return json.dumps({"exit_code": 1, "response": "  role %s does not exist" % options["name"]})


def plugin_roles_list(user, action, options):
    result = ""
    cursor = bandicoot.cli.api.db.roles.find()
    for doc in list(cursor):
        for key in sorted(doc):
            if key not in ["_id"]:
                result += '  %s="%s" ' % (key, doc[key])
        result += "\n"
    return json.dumps({"exit_code": 0, "response": result.rstrip()}) # Do not return the last character (carrage return)


@options_required(option_list=["name"])
@options_validator(option_list=["name"], regexp=r'^[a-zA-Z0-9_\-]+$')
def plugin_secrets_add(user, action, options):
    result = bandicoot.cli.api.db.secrets.find_one({"name": options["name"]})
    if result is None:
        post = options
        bandicoot.cli.api.db.secrets.insert_one(post)
        return json.dumps({"exit_code": 0, "response": "  created secret %s" % options["name"]})
    else:
        return json.dumps({"exit_code": 1, "response": "  secret %s already exists" % options["name"]})


@options_required(option_list=["name"])
@options_validator(option_list=["name"], regexp=r'^[a-zA-Z0-9_\-]+$')
def plugin_secrets_edit(user, action, options):
    result = bandicoot.cli.api.db.secrets.update_one({"name": options["name"]},
            {"$set": options})
    if result.matched_count > 0:
        return json.dumps({"exit_code": 0, "response": "  modified secret %s" % options["name"]})
    else:
        return json.dumps({"exit_code": 1, "response": "  secret %s does not exist" % options["name"]})


@options_supported(option_list=["name"])
@options_required(option_list=["name"])
@options_validator(option_list=["name"], regexp=r'^[a-zA-Z0-9_\-]+$')
def plugin_secrets_del(user, action, options):
    post = {"name": options["name"]}
    result = bandicoot.cli.api.db.secrets.delete_many(post)
    if result.deleted_count > 0:
        return json.dumps({"exit_code": 0, "response": "  deleted secret %s" % options["name"]})
    else:
        return json.dumps({"exit_code": 1, "response": "  secret %s does not exist" % options["name"]})


@options_supported(option_list=["oldpw"])
def plugin_secrets_encryptpw(user, action, options):
    def update_secret_pw(name, options):
        result = bandicoot.cli.api.db.secrets.update_one({"name": name},
                {"$set": options})
        if result.matched_count > 0:
            return True
        else:
            return False
    result = ""
    cursor = bandicoot.cli.api.db.secrets.find()
    # secrets encryptpw --- encrypt clear text pw using the current password
    # secrets encryptpw oldpw=XXXX --- re-encrypt secrets that use oldpw to use the current password
    for doc in list(cursor):
        if "secret" in doc:
            # Detect status of secret
            decrypted_secret = ""
            encrypted_secret = None
            what_to_do = "nothing"
            old_encrypt_password = None # Default assumes secret is clear text, if no oldpw is provided this is assumed
            new_encrypt_password = None # use global pw
            if options is not None and "oldpw" in options:
                # Old password provided, so use it
                old_encrypt_password = str(options["oldpw"])


            # Detect The Problem With Decryption
            try:
                decrypted_secret = bandicoot.cli.api.decrypt_str(doc["secret"], encrypt_password=new_encrypt_password)
            except DecryptWrongKeyException:
                # P
                what_to_do = "updatepw"
            except DecryptNotClearTextException:
                # User said it was clear text, but its not. Skip, Do Nothing.
                what_to_do = "notcleartext"
            # Prefix is "__bandicoot_encrypted__:"
            if decrypted_secret == doc["secret"][len("__bandicoot_encrypted__:"):]:
                # Clear text to encrypted
                what_to_do = "encrypt"

            if what_to_do == "updatepw":
                try:
                    decrypted_secret = bandicoot.cli.api.decrypt_str(doc["secret"], encrypt_password=old_encrypt_password)
                except DecryptException:
                    result += "secret %s failed to update to new password\n" % doc["name"]
                    continue
                encrypted_secret = bandicoot.cli.api.encrypt_str(decrypted_secret, new_encrypt_password)
                result += "secret %s updated to new password\n" % doc["name"]
            elif what_to_do == "encrypt":
                try:
                    decrypted_secret = bandicoot.cli.api.decrypt_str(doc["secret"], encrypt_password=old_encrypt_password)
                except DecryptException:
                    result += "secret %s failed to update because the secret is not clear text\n" % doc["name"]
                    continue
                encrypted_secret = bandicoot.cli.api.encrypt_str(decrypted_secret, new_encrypt_password)
                result += "secret %s encrypted using new password\n" % doc["name"]

            # Secret Was Updated
            if encrypted_secret is not None:
                update_secret_pw(doc["name"], {"secret": encrypted_secret})

    return json.dumps({"exit_code": 0, "response": result})


def plugin_secrets_list(user, action, options):
    result = ""
    cursor = bandicoot.cli.api.db.secrets.find()
    for doc in list(cursor):
        if "secret" in doc:
            # Detect status of secret
            decrypted_secret = ""
            doc["status"] = "encrypted"
            try:
                decrypted_secret = bandicoot.cli.api.decrypt_str(doc["secret"])
            except DecryptWrongKeyException:
                doc["status"] = "wrongpw"
            except DecryptNotClearTextException:
                doc["status"] = "noencryptpw"
            # Prefix is "__bandicoot_encrypted__:"
            if decrypted_secret == doc["secret"][len("__bandicoot_encrypted__:"):]:
                doc["status"] = "cleartext"

            # Do Not Print Encrypted Secret
            doc["secret"] = "..."
        for key in sorted(doc):
            if key not in ["_id"]:
                result += '  %s="%s" ' % (key, doc[key])
        result += "\n"
    return json.dumps({"exit_code": 0, "response": result.rstrip()}) # Do not return the last character (carrage return)


def plugin_plugins_list(user, action, options):
    return json.dumps({"exit_code": 0, "response": "\n  ".join(bandicoot.cli.api.plugins.keys())})


def plugin_logs(user, action, options):
    result = ""

    # Index is required because of the sorting
    # Not sure if this should be done at each call or only once when the first log is created
    bandicoot.cli.api.db.logs.create_index([("date", 1)])
    bandicoot.cli.api.db.inventory.changes.create_index([("date", 1)])

    if options is not None and ("name" in options or ("type" in options and options["type"] == "changes")):
        # List changes/logs for a specific inventory host
        result += "  inventory_item\t\tdesc\t\tjob_id\t\tdate\n"
        if "name" in options:
            # Show changes for a specific inventory item
            cursor = bandicoot.cli.api.db.inventory.changes.find({"name": options["name"]}).sort("date", 1)
        else:
            # Show all changes
            cursor = bandicoot.cli.api.db.inventory.changes.find().sort("date", 1)
        for doc in list(cursor):
            if "date" in doc: # Backward compat
                result += '  %s\t"%s"\t%s\t%s\n' % (doc["name"], doc["desc"], doc["job_id"], "{:%m/%d/%Y %M:%H}".format(doc["date"]))
    else: # type=requests is the default
        # Default List all requests to api server
        result += "  category\t\taction\t\toptions\t\tdate\n"
        cursor = bandicoot.cli.api.db.logs.find().sort("date", 1)
        for doc in list(cursor):
            # Backward compat when user field did not exist
            if "user" not in doc:
                doc["user"] = "unknown"
            # Backward compat when result field did not exist
            if "result" not in doc:
                doc["result"] = "unknown"
            # Backward compat when date field did not exist
            if "date" not in doc:
                doc["date"] = datetime.date(1970, 1, 1) # unknown
            result += "  %s\t%s\t%s\t%s\t%s\n" % (doc["user"], doc["category"], doc["action"], doc["options"], "{:%m/%d/%Y %M:%H}".format(doc["date"]))
    return json.dumps({"exit_code": 0, "response": result})


@queue_support()
def plugin_ansible(user, action, options, exit_event, q):
    def process_stdout(p, q):
        for line in p.stderr:
            q.put("  %s\n" % line)
        for line in p.stdout:
            q.put("  %s\n" % line)
        p.wait()
        #time.sleep(0.1) # Delay For Queue Operations
        return 0

    ansible_options = ""
    temp_location = "/tmp/bandicoot/%s" % str(time.time())

    # Required options to be included in action
    for option in ["source_url", "playbook"]:
        if option not in action:
            return json.dumps({"exit_code": 1, "response": "  %s required in action" % option})

    # Sudo
    if "sudo" in action and action["sudo"] == "yes":
        ansible_options += "-s "

    # Git
    cmd = str("git clone %s %s" % (action["source_url"], temp_location)).split()
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    thread = threading.Thread(target=process_stdout, args=(p,q))
    thread.start()
    while thread.isAlive() and not exit_event.is_set():
        time.sleep(0.25)

    if thread.isAlive():
        p.kill()

    time.sleep(0.25)
    thread.join()

    # Ansible
    cmd = str("ansible-playbook %s %s" % (ansible_options, action["playbook"])).split()
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=temp_location)
    thread = threading.Thread(target=process_stdout, args=(p,q))
    thread.start()
    while thread.isAlive() and not exit_event.is_set():
        time.sleep(0.25)

    if thread.isAlive():
        p.kill()

    time.sleep(0.25)
    thread.join()

    # Delete temporary git directory
    if os.path.isdir(temp_location):
        shutil.rmtree(temp_location)

    q.put(EOF)
    time.sleep(0.1) # Delay For Queue
    #sys.exit(0)
    return json.dumps({"exit_code": 0, "response": "  success"}) # For unittesting


@options_supported(option_list=["id"])
@options_required(option_list=["id"])
@options_validator(option_list=["id"], regexp=r'^[0-9]+$')
def plugin_jobs_status(user, action, options):
    global job_queue
    exit_code = 0

    result = bandicoot.cli.api.db.jobs.find_one({"_id": int(options["id"])})
    if result is None:
        exit_code = 1
        return json.dumps({"exit_code": 1, "response": "  The job id %s does not match a job" % str(options["id"]), "exit_code": exit_code})
    else:
        int_id = int(options["id"])
        if result["user"] != user:
            exit_code = 1
            return json.dumps({"exit_code": 1, "response": "  The job %s, is owned by another user" % str(int_id), "exit_code": exit_code})

        # Get all items from queue until its empty or EOF is reached
        while True:
            try:
                if result["_id"] not in job_queue:
                    result["running"] = False
                    bandicoot.cli.api.db.jobs.update_one({"_id": result["_id"]}, {"$set": {"running": result["running"]},})
                    # Job already ran, just return the result
                    break

                qitem = job_queue[result["_id"]]["queue"].get_nowait()
                if qitem != EOF:
                    # New Data from job!
                    result["response"] += qitem
                    bandicoot.cli.api.db.jobs.update_one({"_id": result["_id"]}, {"$set": {"response": result["response"]},})
                else:
                    # EOF, job is finished
                    result["running"] = False
                    bandicoot.cli.api.db.jobs.update_one({"_id": result["_id"]}, {"$set": {"running": result["running"]},})
                    result["end_time"] = time.time()
                    bandicoot.cli.api.db.jobs.update_one({"_id": result["_id"]}, {"$set": {"end_time": result["end_time"]},})

                    # Discover New Inventory
                    tmp_hosts = {}
                    current_task_name = "unknown"

                    for line in result["response"].split("\n"):
                        line = line.strip()
                        line = line.strip("\n")
                        # Match Task name, example:   TASK [setup] *******************************************************************
                        m = re.match(r'^\s*TASK\s+\[(.*?)\]', line)
                        if m:
                            current_task_name = m.group(1)
                        # Match changed|ok|skipped|fatal, example:   ok: [ec2-52-89-49-1.us-west-2.compute.amazonaws.com]
                        m = re.match(r'^\s*([a-z]+):\s+\[(.*?)\]', line)
                        if m:
                            change_state = m.group(1)
                            hostname = m.group(2)
                            if hostname not in tmp_hosts:
                                tmp_hosts[hostname] = []
                            if change_state == "changed" or change_state == "fatal": # Only log changes or failed changes
                                tmp_hosts[hostname].append({"name": hostname, "date": datetime.datetime.utcnow(), "desc": current_task_name, "job_id": result["_id"]})

                    for hostname in tmp_hosts:
                        dbresult = bandicoot.cli.api.db.inventory.hosts.find_one({"name": hostname})
                        if dbresult is None:
                            # New Inventory Item discovered
                            bandicoot.cli.api.db.inventory.hosts.insert_one({"name": hostname})

                        # Log Inventory Changelog
                        for document in tmp_hosts[hostname]:
                            bandicoot.cli.api.db.inventory.changes.insert_one(document)

                    break
            except Queue.Empty:
                break

        return json.dumps({"response": result["response"], "finished": not result["running"], "exit_code": exit_code})


def plugin_jobs_list(user, action, options):
    result = "  Job ID\tIs Running?\tUser\tCommand\n"
    api_result = []
    cursor = bandicoot.cli.api.db.jobs.find()
    for doc in list(cursor):
        is_running = doc["_id"] in job_queue and doc["running"]
        api_result.append({"_id": doc["_id"], "is_running": is_running, "user": doc["user"], "category": doc["action"]["category"], "action": doc["action"]["action"]})
        result += "  %s\t\t%s\t\t%s\t\t%s/%s\n" % (str(doc["_id"]), str(is_running),
                                              str(doc["user"]),
                                              str(doc["action"]["category"]).rstrip("/"),
                                              str(doc["action"]["action"]))

    return json.dumps({"exit_code": 0, "response": result, "api_response": api_result})


@options_supported(option_list=["id"])
@options_required(option_list=["id"])
@options_validator(option_list=["id"], regexp=r'^[0-9]+$')
def plugin_jobs_kill(user, action, options):
    global job_queue
    
    result = bandicoot.cli.api.db.jobs.find_one({"_id": int(options["id"])})
    if result is None:
        return json.dumps({"exit_code": 1, "response": "  The job id %s does not match a job" % str(options["id"])})
    else:
        int_id = int(options["id"])
        if result["running"] == False:
            return json.dumps({"exit_code": 1, "response": "  The job %s, was already terminated" % str(int_id)})
        elif result["user"] != user:
            return json.dumps({"exit_code": 1, "response": "  The job %s, is owned by another user" % str(int_id)})
        job_queue[int_id]["exit_event"].set() # Set event to trigger exit
        job_queue[int_id]["process"].join() # Wait for Plugin to exit
        result["running"] = False
        bandicoot.cli.api.db.jobs.update_one({"_id": result["_id"]}, {"$set": {"running": result["running"]},})
        return json.dumps({"exit_code": 0, "response": "  The job %s, was terminated" % str(int_id)})


@options_supported(option_list=["name", "user", "category", "action", "minute", "hour", "day_of_month", "month", "day_of_week"])
@options_required(option_list=["name", "category", "action"])
@options_validator(option_list=["name", "user", "action"], regexp=r'^[a-zA-Z0-9_\-]+$')
@options_validator(option_list=["category"], regexp=r'^[/a-zA-Z0-9_\-]+$')
@options_validator(option_list=["minute", "hour", "day_of_month", "month", "day_of_week"], regexp=r'^([0-9]+|\*)$')
def plugin_schedules_add(user, action, options):
    result = bandicoot.cli.api.db.schedules.find_one({"name": options["name"]})
    if result is None:
        post = options
        # Prevent Users from setting up crons for other users
        if "user" in post and post["user"] != user:
            return json.dumps({"exit_code": 1, "response": "  You cannot set the cron user to anyone but your username %s." % user})
        # Always set the cron by default to run as the user
        if "user" not in post:
            post["user"] = user

        bandicoot.cli.api.db.schedules.insert_one(post)
        return json.dumps({"exit_code": 0, "response": "  created schedule %s" % options["name"]})
    else:
        return json.dumps({"exit_code": 1, "response": "  schedule %s already exists" % options["name"]})


@options_supported(option_list=["name", "user", "category", "action", "minute", "hour", "day_of_month", "month", "day_of_week"])
@options_required(option_list=["name"])
@options_validator(option_list=["name", "user", "action"], regexp=r'^[a-zA-Z0-9_\-]+$')
@options_validator(option_list=["category"], regexp=r'^[/a-zA-Z0-9_\-]+$')
@options_validator(option_list=["minute", "hour", "day_of_month", "month", "day_of_week"], regexp=r'^([0-9]+|\*)$')
def plugin_schedules_edit(user, action, options):
    # Prevent Users from setting up crons for other users
    if "user" in options and options["user"] != user:
        return json.dumps({"exit_code": 1, "response": "  You cannot set the cron user to anyone but your username %s." % user})

    result = bandicoot.cli.api.db.schedules.update_one({"name": options["name"]},
            {"$set": options})
    if result.matched_count > 0:
        return json.dumps({"exit_code": 0, "response": "  modified schedule %s" % options["name"]})
    else:
        return json.dumps({"exit_code": 1, "response": "  schedule %s does not exist" % options["name"]})


@options_supported(option_list=["name"])
@options_required(option_list=["name"])
@options_validator(option_list=["name"], regexp=r'^[a-zA-Z0-9_\-]+$')
def plugin_schedules_del(user, action, options):
    post = {"name": options["name"]}
    result = bandicoot.cli.api.db.schedules.delete_many(post)
    if result.deleted_count > 0:
        return json.dumps({"exit_code": 0, "response": "  deleted schedule %s" % options["name"]})
    else:
        return json.dumps({"exit_code": 1, "response": "  schedule %s does not exist" % options["name"]})


def plugin_schedules_list(user, action, options):
    result = ""
    cursor = bandicoot.cli.api.db.schedules.find()
    for doc in list(cursor):
        for key in sorted(doc):
            if key not in ["_id"]:
                result += '  %s="%s" ' % (key, doc[key])
        result += "\n"
    return json.dumps({"exit_code": 0, "response": result.rstrip()}) # Do not return the last character (carrage return)


def plugin_inventory_list(user, action, options):
    result = ""
    cursor = bandicoot.cli.api.db.inventory.hosts.find()
    for doc in list(cursor):
        result += "  %s\n" % doc["name"]
    return json.dumps({"exit_code": 0, "response": result.rstrip()}) # Do not return the last character (carrage return)


@options_supported(option_list=["name"])
@options_required(option_list=["name"])
def plugin_inventory_del(user, action, options):
    post = {"name": options["name"]}
    result = bandicoot.cli.api.db.inventory.hosts.delete_many(post)
    if result.deleted_count > 0:
        return json.dumps({"exit_code": 0, "response": "  deleted inventory item %s" % options["name"]})
    else:
        return json.dumps({"exit_code": 1, "response": "  inventory item %s does not exist" % options["name"]})


@options_supported(option_list=["type"])
def plugin_stats(user, action, options):
    from ascii_graph import Pyasciigraph
    response = ""
    stat_data = []
    stat_type = "users"
    stat_title = ""
    stat_type_supported = ("users", "system", "jobs")
    if options is not None and "type" in options and options["type"] in stat_type_supported:
        stat_type = options["type"]

    # Sum up Job By User
    if stat_type == "users":
        stat_title = "Jobs Submitted Per User"
        user_stats = {}
        cursor = bandicoot.cli.api.db.jobs.find()
        for doc in list(cursor):
            if doc["user"] not in user_stats:
                user_stats[doc["user"]] = 1
            else:
                user_stats[doc["user"]] += 1
        stat_data = [(k, v) for k, v in user_stats.iteritems()] # Convert Dict to List of Tuples
    elif stat_type == "system":
        stat_title = "Changes Per Inventory Item"
        system_stats = {}
        cursor = bandicoot.cli.api.db.inventory.changes.find().sort("date", 1)
        for doc in list(cursor):
            if doc["name"] not in system_stats:
                system_stats[doc["name"]] = 1
            else:
                system_stats[doc["name"]] += 1
        stat_data = [(k, v) for k, v in system_stats.iteritems()] # Convert Dict to List of Tuples
    elif stat_type == "jobs":
        stat_title = "Jobs Submitted By Date"
        job_stats = {}
        cursor = bandicoot.cli.api.db.inventory.changes.find().sort("date", 1)
        for doc in list(cursor):
            if "date" in doc:
                doc_date = "{:%m/%d/%Y}".format(doc["date"])
                if doc_date not in job_stats:
                    job_stats[doc_date] = 1
                else:
                    job_stats[doc_date] += 1
        stat_data = [(k, v) for k, v in job_stats.iteritems()] # Convert Dict to List of Tuples

    # Graph Data
    graph = Pyasciigraph()
    for line in graph.graph(stat_title, stat_data):
        response += "%s\n" % line

    return json.dumps({"exit_code": 0, "response": "  %s" % response})
