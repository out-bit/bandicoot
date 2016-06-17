import outbit.cli.api
import json
import subprocess
import hashlib
import datetime


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


def plugin_actions_add(user, action, options):
    dat = None

    for requiredopt in ["name", "category", "action", "plugin"]:
        if requiredopt not in options:
            dat = json.dumps({"response": "  %s option is required" % requiredopt})
            return dat

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


def plugin_actions_edit(user, action, options):
    if "name" not in options:
        return json.dumps({"response": "  name option is required"})
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
        #result += "  %s\n" % doc["name"]
        result += "  %s\n" % doc
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
        result += "  %s\n" % doc
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
        doc["secret"] = "..." # do not print encrypted secret
        result += "  %s\n" % doc
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