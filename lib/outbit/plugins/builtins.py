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


running_queue = {}
running_queue_count = 0
EOF = -1


def queue_support():
    def wrap(f):
        def wrapped_f(*args):
            global running_queue
            global running_queue_count
            user = args[0]
            action = args[1]
            options = args[2]
            queue_id = running_queue_count
            q = multiprocessing.Queue()
            p = multiprocessing.Process(target=f, args=args+(q,))
            running_queue[queue_id] = {"start_time": time.time(), "user": user, "action": action, "options": options, "queue": q, "process": p, "running": True, "response": ""}
            running_queue_count += 1
            p.start()
            return json.dumps({"queue_id": queue_id})
        return wrapped_f
    return wrap


def options_validator(option_list, regexp):
    def wrap(f):
        def wrapped_f(*args):
            user = args[0]
            action = args[1]
            options = args[2]
            for key in options:
                if key in option_list and not re.match(regexp, options[key]):
                    return json.dumps({"response": "  option %s=%s has invalid characters" % (key, options[key])})
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


def plugin_users_add(user, action, options):
    if "username" not in options or "password" not in options:
        return json.dumps({"response": "  username and password are required options"})
    else:
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


def plugin_users_del(user, action, options):
    if "username" not in options:
        return json.dumps({"response": "  username option is required"})
    post = {"username": options["username"]}
    result = outbit.cli.api.db.users.delete_many(post)
    if result.deleted_count > 0:
        return json.dumps({"response": "  deleted user %s" % options["username"]})
    else:
        return json.dumps({"response": "  user %s does not exist" % options["username"]})


def plugin_users_edit(user, action, options):
    if "username" not in options:
        return json.dumps({"response": "  username option is required"})
    if "password" not in options:
        return json.dumps({"response": "  password option is required"})
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


@options_validator(option_list=["name", "plugin", "action"], regexp=r'^[a-zA-Z0-9_\-]+$')
@options_validator(option_list=["category"], regexp=r'^[a-zA-Z0-9_\-/]+$')
def plugin_actions_add(user, action, options):
    dat = None

    for requiredopt in ["name", "category", "action", "plugin", "desc"]:
        if requiredopt not in options:
            dat = json.dumps({"response": "  %s option is required" % requiredopt})
            return dat

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


@options_validator(option_list=["name", "plugin", "action"], regexp=r'^[a-zA-Z0-9_\-]+$')
@options_validator(option_list=["category"], regexp=r'^[a-zA-Z0-9_\-/]+$')
def plugin_actions_edit(user, action, options):
    if "name" not in options:
        return json.dumps({"response": "  name option is required"})

    category_fix(options)

    result = outbit.cli.api.db.actions.update_one({"name": options["name"]},
            {"$set": options})
    if result.matched_count > 0:
        return json.dumps({"response": "  modified action %s" % options["name"]})
    else:
        return json.dumps({"response": "  action %s does not exist" % options["name"]})


def plugin_actions_del(user, action, options):
    dat = None

    if "name" not in options:
        return json.dumps({"response": "  name option is required"})

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


def plugin_roles_add(user, action, options):
    if "name" not in options:
        return json.dumps({"response": "  name option is required"})
    else:
        result = outbit.cli.api.db.roles.find_one({"name": options["name"]})
        if result is None:
            post = options
            outbit.cli.api.db.roles.insert_one(post)
            return json.dumps({"response": "  created role %s" % options["name"]})
        else:
            return json.dumps({"response": "  role %s already exists" % options["name"]})


def plugin_roles_edit(user, action, options):
    if "name" not in options:
        return json.dumps({"response": "  name option is required"})
    result = outbit.cli.api.db.roles.update_one({"name": options["name"]},
            {"$set": options})
    if result.matched_count > 0:
        return json.dumps({"response": "  modified role %s" % options["name"]})
    else:
        return json.dumps({"response": "  role %s does not exist" % options["name"]})


def plugin_roles_del(user, action, options):
    if "name" not in options:
        return json.dumps({"response": "  name option is required"})
    else:
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


def plugin_secrets_add(user, action, options):
    if "name" not in options:
        return json.dumps({"response": "  name option is required"})
    else:
        result = outbit.cli.api.db.secrets.find_one({"name": options["name"]})
        if result is None:
            post = options
            outbit.cli.api.db.secrets.insert_one(post)
            return json.dumps({"response": "  created secret %s" % options["name"]})
        else:
            return json.dumps({"response": "  secret %s already exists" % options["name"]})


def plugin_secrets_edit(user, action, options):
    if "name" not in options:
        return json.dumps({"response": "  name option is required"})
    result = outbit.cli.api.db.secrets.update_one({"name": options["name"]},
            {"$set": options})
    if result.matched_count > 0:
        return json.dumps({"response": "  modified secret %s" % options["name"]})
    else:
        return json.dumps({"response": "  secret %s does not exist" % options["name"]})


def plugin_secrets_del(user, action, options):
    if "name" not in options:
        return json.dumps({"response": "  name option is required"})
    else:
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
    shutil.rmtree(temp_location)

    q.put(EOF)
    sys.exit(0)


def plugin_jobs_status(user, action, options):
    if options is None or "id" not in options:
        # In this case, outbit_error is required! 
        # This string is used by the client to determine if an error ocurred
        return json.dumps({"response": "  outbit_error: id option is required"})
    elif int(options["id"]) not in running_queue:
        return json.dumps({"response": "  outbit_error: id does not match a job"})
    else:
        int_id = int(options["id"])
        if running_queue[int_id]["user"] != user:
            return json.dumps({"response": "  The job %s, is owned by another user" % str(int_id)})
        try:
            qitem = running_queue[int_id]["queue"].get_nowait()
            if qitem != EOF: 
                # New Data from job!
                running_queue[int_id]["response"] += qitem
            else:
                # EOF, job is finished
                running_queue[int_id]["running"] = False
                running_queue[int_id]["end_time"] = time.time()
                return json.dumps({"response": EOF})
        except Queue.Empty:
            pass

        return json.dumps({"response": running_queue[int_id]["response"]})


def plugin_jobs_list(user, action, options):
    result = "  Job ID\tIs Running?\tUser\tCommand\n"
    for job_id in running_queue:
        result += "  %s\t\t%s\t\t%s\t\t%s/%s\n" % (str(job_id), str(running_queue[job_id]["running"]),
                                              str(running_queue[job_id]["user"]),
                                              str(running_queue[job_id]["action"]["category"]).rstrip("/"),
                                              str(running_queue[job_id]["action"]["action"]))

    return json.dumps({"response": result})


def plugin_jobs_kill(user, action, options):
    if options is None or "id" not in options:
        return json.dumps({"response": "  outbit_error: id option is required"})
    elif int(options["id"]) not in running_queue:
        return json.dumps({"response": "  outbit_error: id does not match a job"})
    else:
        int_id = int(options["id"])
        if running_queue[int_id]["running"] == False:
            return json.dumps({"response": "  The job %s, was already terminated" % str(int_id)})
        elif running_queue[int_id]["user"] != user:
            return json.dumps({"response": "  The job %s, is owned by another user" % str(int_id)})
        running_queue[int_id]["process"].terminate()
        running_queue[int_id]["running"] = False
        return json.dumps({"response": "  The job %s, was terminated" % str(int_id)})