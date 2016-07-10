import outbit.cli.api
import json
import subprocess
import hashlib
import datetime
import re
import shutil
import time
import multiprocessing
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
            q = multiprocessing.Queue()
            p = multiprocessing.Process(target=f, args=args+(q,))
            job_id = int(outbit.cli.api.counters_db_getNextSequence("jobid"))
            outbit.cli.api.db.jobs.insert_one({"_id": int(job_id), "start_time": time.time(), "user": user, "action": action, "options": options, "running": True, "response": ""})
            job_queue[job_id] = { "queue": q, "process": p }
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
                        return json.dumps({"response": "  option %s=%s has invalid characters" % (key, options[key])})
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
                        return json.dumps({"response": "  %s option is required" % key})
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
                        return json.dumps({"response": "  %s option is not supported. Supported options are: %s." % (key, ", ".join(option_list))})
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
    cursor = outbit.cli.api.db.actions.find()
    response = ""
    for dbaction in outbit.cli.api.builtin_actions + list(cursor):
        if outbit.cli.api.roles_has_permission(user, {"category": dbaction["category"], "action": dbaction["action"]}, {}):
            category_str = dbaction["category"].strip("/").replace("/", " ")
            if category_str is None or len(category_str) <= 0:
                response += "  %s \t\t\t%-60s\n" % (dbaction["action"], dbaction["desc"])
            else:
                response += "  %s %s \t\t%-60s\n" % (dbaction["category"].strip("/").replace("/", " "), dbaction["action"], dbaction["desc"])

    # Append the exit builtin implemented on the client side
    response += "  exit \t\t\n"

    return json.dumps({"response": response})


def plugin_ping(user, action, options):
    return json.dumps({"response": "  pong"})


@options_supported(option_list=["username", "password"])
@options_required(option_list=["username", "password"])
@options_validator(option_list=["username"], regexp=r'^[a-zA-Z0-9_\-]+$')
def plugin_users_add(user, action, options):
    result = outbit.cli.api.db.users.find_one({"username": options["username"]})
    if result is None:
        m = hashlib.md5()
        m.update(str(options["password"]))
        password_md5 = str(m.hexdigest())
        post = {"username": options["username"], "password_md5": password_md5}
        outbit.cli.api.db.users.insert_one(post)
        return json.dumps({"response": "  created user %s" % options["username"]})
    else:
        return json.dumps({"response": "  user %s already exists" % options["username"]})


@options_supported(option_list=["username"])
@options_required(option_list=["username"])
@options_validator(option_list=["username"], regexp=r'^[a-zA-Z0-9_\-]+$')
def plugin_users_del(user, action, options):
    post = {"username": options["username"]}
    result = outbit.cli.api.db.users.delete_many(post)
    if result.deleted_count > 0:
        return json.dumps({"response": "  deleted user %s" % options["username"]})
    else:
        return json.dumps({"response": "  user %s does not exist" % options["username"]})


@options_supported(option_list=["username", "password"])
@options_required(option_list=["username", "password"])
@options_validator(option_list=["username"], regexp=r'^[a-zA-Z0-9_\-]+$')
def plugin_users_edit(user, action, options):
    m = hashlib.md5()
    m.update(options["password"])
    password_md5 = str(m.hexdigest())
    result = outbit.cli.api.db.users.update_one({"username": options["username"]},
            {"$set": {"password_md5": password_md5},})
    if result.matched_count > 0:
        return json.dumps({"response": "  modified user %s" % options["username"]})
    else:
        return json.dumps({"response": "  user %s does not exist" % options["username"]})


def plugin_users_list(user, action, options):
    result = ""
    cursor = outbit.cli.api.db.users.find()
    for doc in list(cursor):
        result += "  %s\n" % doc["username"]
    return json.dumps({"response": result.rstrip()}) # Do not return the last character (carrage return)


@options_required(option_list=["name", "category", "action", "plugin", "desc"])
@options_validator(option_list=["name", "plugin", "action"], regexp=r'^[a-zA-Z0-9_\-]+$')
@options_validator(option_list=["category"], regexp=r'^[a-zA-Z0-9_\-/]+$')
def plugin_actions_add(user, action, options):
    dat = None

    category_fix(options)

    find_result = outbit.cli.api.db.actions.find_one({"name": options["name"]})
    if find_result is None:
        result = outbit.cli.api.db.actions.insert_one(options)
        dat = json.dumps({"response": "  created action %s" % options["name"]})
    else:
        dat = json.dumps({"response": "  action %s already exists" % options["name"]})
    return dat


def plugin_command(user, action, options):
    result = ""
    if "command_run" not in action:
        return json.dumps({"response": "  command_run required in action"})
    cmd = action["command_run"].split()
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    for line in p.stdout:
        result += "  %s\n" % line
    p.wait()
    result += "  return code: %d\n"  % p.returncode
    return json.dumps({ "response": result})


@options_required(option_list=["name"])
@options_validator(option_list=["name", "plugin", "action"], regexp=r'^[a-zA-Z0-9_\-]+$')
@options_validator(option_list=["category"], regexp=r'^[a-zA-Z0-9_\-/]+$')
def plugin_actions_edit(user, action, options):
    category_fix(options)

    result = outbit.cli.api.db.actions.update_one({"name": options["name"]},
            {"$set": options})
    if result.matched_count > 0:
        return json.dumps({"response": "  modified action %s" % options["name"]})
    else:
        return json.dumps({"response": "  action %s does not exist" % options["name"]})


@options_supported(option_list=["name"])
@options_required(option_list=["name"])
@options_validator(option_list=["name"], regexp=r'^[a-zA-Z0-9_\-]+$')
def plugin_actions_del(user, action, options):
    dat = None

    post = {"name": options["name"]}
    result = outbit.cli.api.db.actions.delete_many(post)
    if result.deleted_count > 0:
        dat = json.dumps({"response": "  deleted action %s" % options["name"]})
    else:
        dat = json.dumps({"response": "  action %s does not exist" % options["name"]})
    return dat


def plugin_actions_list(user, action, options):
    result = ""
    cursor = outbit.cli.api.db.actions.find()
    for doc in list(cursor):
        for key in sorted(doc):
            if key not in ["_id"]:
                result += '  %s="%s" ' % (key, doc[key])
        result += "\n"
    return json.dumps({"response": result.rstrip()}) # Do not return the last character (carrage return)


@options_required(option_list=["name"])
@options_validator(option_list=["name"], regexp=r'^[a-zA-Z0-9_\-]+$')
def plugin_roles_add(user, action, options):
    result = outbit.cli.api.db.roles.find_one({"name": options["name"]})
    if result is None:
        post = options
        outbit.cli.api.db.roles.insert_one(post)
        return json.dumps({"response": "  created role %s" % options["name"]})
    else:
        return json.dumps({"response": "  role %s already exists" % options["name"]})


@options_required(option_list=["name"])
@options_validator(option_list=["name"], regexp=r'^[a-zA-Z0-9_\-]+$')
def plugin_roles_edit(user, action, options):
    result = outbit.cli.api.db.roles.update_one({"name": options["name"]},
            {"$set": options})
    if result.matched_count > 0:
        return json.dumps({"response": "  modified role %s" % options["name"]})
    else:
        return json.dumps({"response": "  role %s does not exist" % options["name"]})


@options_supported(option_list=["name"])
@options_required(option_list=["name"])
@options_validator(option_list=["name"], regexp=r'^[a-zA-Z0-9_\-]+$')
def plugin_roles_del(user, action, options):
    post = {"name": options["name"]}
    result = outbit.cli.api.db.roles.delete_many(post)
    if result.deleted_count > 0:
        return json.dumps({"response": "  deleted role %s" % options["name"]})
    else:
        return json.dumps({"response": "  role %s does not exist" % options["name"]})


def plugin_roles_list(user, action, options):
    result = ""
    cursor = outbit.cli.api.db.roles.find()
    for doc in list(cursor):
        for key in sorted(doc):
            if key not in ["_id"]:
                result += '  %s="%s" ' % (key, doc[key])
        result += "\n"
    return json.dumps({"response": result.rstrip()}) # Do not return the last character (carrage return)


@options_required(option_list=["name"])
@options_validator(option_list=["name"], regexp=r'^[a-zA-Z0-9_\-]+$')
def plugin_secrets_add(user, action, options):
    result = outbit.cli.api.db.secrets.find_one({"name": options["name"]})
    if result is None:
        post = options
        outbit.cli.api.db.secrets.insert_one(post)
        return json.dumps({"response": "  created secret %s" % options["name"]})
    else:
        return json.dumps({"response": "  secret %s already exists" % options["name"]})


@options_required(option_list=["name"])
@options_validator(option_list=["name"], regexp=r'^[a-zA-Z0-9_\-]+$')
def plugin_secrets_edit(user, action, options):
    result = outbit.cli.api.db.secrets.update_one({"name": options["name"]},
            {"$set": options})
    if result.matched_count > 0:
        return json.dumps({"response": "  modified secret %s" % options["name"]})
    else:
        return json.dumps({"response": "  secret %s does not exist" % options["name"]})


@options_supported(option_list=["name"])
@options_required(option_list=["name"])
@options_validator(option_list=["name"], regexp=r'^[a-zA-Z0-9_\-]+$')
def plugin_secrets_del(user, action, options):
    post = {"name": options["name"]}
    result = outbit.cli.api.db.secrets.delete_many(post)
    if result.deleted_count > 0:
        return json.dumps({"response": "  deleted secret %s" % options["name"]})
    else:
        return json.dumps({"response": "  secret %s does not exist" % options["name"]})


def plugin_secrets_list(user, action, options):
    result = ""
    cursor = outbit.cli.api.db.secrets.find()
    for doc in list(cursor):
        if "secret" in doc:
            doc["secret"] = "..." # do not print encrypted secret
        for key in sorted(doc):
            if key not in ["_id"]:
                result += '  %s="%s" ' % (key, doc[key])
        result += "\n"
    return json.dumps({"response": result.rstrip()}) # Do not return the last character (carrage return)


def plugin_plugins_list(user, action, options):
    return json.dumps({"response": "\n  ".join(outbit.cli.api.plugins.keys())})


def plugin_logs(user, action, options):
    result = "  category\t\taction\t\toptions\n"
    cursor = outbit.cli.api.db.logs.find().sort("date", 1)
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
    return json.dumps({"response": result})


@queue_support()
def plugin_ansible(user, action, options, q):
    ansible_options = ""
    temp_location = "/tmp/outbit/%s" % str(time.time())

    # Required options to be included in action
    for option in ["source_url", "playbook"]:
        if option not in action:
            return json.dumps({"response": "  %s required in action" % option})

    # Sudo
    if "sudo" in action and action["sudo"] == "yes":
        ansible_options += "-s "

    # Git
    cmd = str("git clone %s %s" % (action["source_url"], temp_location)).split()
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for line in p.stderr:
        q.put("  %s\n" % line)
    p.wait()

    # Ansible
    cmd = str("ansible-playbook %s %s" % (ansible_options, action["playbook"])).split()
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=temp_location)
    for line in p.stdout:
        q.put("  %s\n" % line)
    p.wait()

    # Delete temporary git directory
    if os.path.isdir(temp_location):
        shutil.rmtree(temp_location)

    q.put(EOF)
    sys.exit(0)
    return json.dumps({"response": "  success"}) # For unittesting


@options_supported(option_list=["id"])
@options_required(option_list=["id"])
@options_validator(option_list=["id"], regexp=r'^[0-9]+$')
def plugin_jobs_status(user, action, options):
    global job_queue

    result = outbit.cli.api.db.jobs.find_one({"_id": int(options["id"])})
    if result is None:
        return json.dumps({"response": "  The job id %s does not match a job" % str(options["id"])})
    else:
        int_id = int(options["id"])
        if result["user"] != user:
            return json.dumps({"response": "  The job %s, is owned by another user" % str(int_id)})

        # Get all items from queue until its empty or EOF is reached
        while True:
            try:
                if result["_id"] not in job_queue:
                    result["running"] = False
                    outbit.cli.api.db.jobs.update_one({"_id": result["_id"]}, {"$set": {"running": result["running"]},})
                    # Job already ran, just return the result
                    break

                qitem = job_queue[result["_id"]]["queue"].get_nowait()
                if qitem != EOF:
                    # New Data from job!
                    result["response"] += qitem
                    outbit.cli.api.db.jobs.update_one({"_id": result["_id"]}, {"$set": {"response": result["response"]},})
                else:
                    # EOF, job is finished
                    result["running"] = False
                    outbit.cli.api.db.jobs.update_one({"_id": result["_id"]}, {"$set": {"running": result["running"]},})
                    result["end_time"] = time.time()
                    outbit.cli.api.db.jobs.update_one({"_id": result["_id"]}, {"$set": {"end_time": result["end_time"]},})
                    break
            except Queue.Empty:
                break

        return json.dumps({"response": result["response"], "finished": not result["running"]})


def plugin_jobs_list(user, action, options):
    result = "  Job ID\tIs Running?\tUser\tCommand\n"
    cursor = outbit.cli.api.db.jobs.find()
    for doc in list(cursor):
        is_running = doc["_id"] in job_queue and doc["running"]
        result += "  %s\t\t%s\t\t%s\t\t%s/%s\n" % (str(doc["_id"]), str(is_running),
                                              str(doc["user"]),
                                              str(doc["action"]["category"]).rstrip("/"),
                                              str(doc["action"]["action"]))

    return json.dumps({"response": result})


@options_supported(option_list=["id"])
@options_required(option_list=["id"])
@options_validator(option_list=["id"], regexp=r'^[0-9]+$')
def plugin_jobs_kill(user, action, options):
    global job_queue
    
    result = outbit.cli.api.db.jobs.find_one({"_id": int(options["id"])})
    if result is None:
        return json.dumps({"response": "  The job id %s does not match a job" % str(options["id"])})
    else:
        int_id = int(options["id"])
        if result["running"] == False:
            return json.dumps({"response": "  The job %s, was already terminated" % str(int_id)})
        elif result["user"] != user:
            return json.dumps({"response": "  The job %s, is owned by another user" % str(int_id)})
        job_queue[int_id]["process"].terminate()
        result["running"] = False
        outbit.cli.api.db.jobs.update_one({"_id": result["_id"]}, {"$set": {"running": result["running"]},})
        return json.dumps({"response": "  The job %s, was terminated" % str(int_id)})