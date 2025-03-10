import nose
import bandicoot
from bandicoot.plugins import builtins
import unittest
import json
import mock
import mongomock
import bandicoot.cli.api
import multiprocessing


class MockPopen(object):
    def __init__(self, stdout, stderr):
        self.stdout = stdout
        self.stderr = stderr

    def wait(self):
        pass

    def kill(self):
        pass


class TestCli(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        bandicoot.cli.api.load_plugins()
        self.mock_db_setup()
        self.mock_db_basic_database()
        bandicoot.cli.api.counters_db_init("jobid") # setup counters in mockdb
        unittest.TestCase.__init__(self, *args, **kwargs)

    def mock_db_setup(self):
        bandicoot.cli.api.dbclient = mongomock.MongoClient()
        bandicoot.cli.api.db = bandicoot.cli.api.dbclient.conn["bandicoot"]

    def mock_db_basic_database(self):
        bandicoot.cli.api.db.users.insert_one({"username": "deleteme", "password_md5": "md5test"})
        bandicoot.cli.api.db.users.insert_one({"username": "jdoe1", "password_md5": "md5test"})
        bandicoot.cli.api.db.users.insert_one({"username": "jdoe2", "password_md5": "md5test"})
        bandicoot.cli.api.db.users.insert_one({"username": "jdoe3", "password_md5": "md5test"})
        bandicoot.cli.api.db.users.insert_one({"username": "jdoe4", "password_md5": "md5test"})

        bandicoot.cli.api.db.actions.insert_one({"name": "deleteme", "category": "/testing", "action": "pwd", "plugin": "command", "command_run": "echo 'hello world'", "desc": "test pwd"})
        bandicoot.cli.api.db.actions.insert_one({"name": "test_action1", "category": "/testing", "action": "pwd", "plugin": "command", "command_run": "echo 'hello world'", "desc": "test pwd"})
        bandicoot.cli.api.db.actions.insert_one({"name": "test_action2", "category": "/testing", "action": "ls", "plugin": "command", "command_run": "echo 'hello world'", "desc": "test ls"})

        bandicoot.cli.api.db.roles.insert_one({"name": "deleteme", "users": "jdoe2", "actions": "/", "secrets": "test_secret1"})
        bandicoot.cli.api.db.roles.insert_one({"name": "test_role1", "users": "jdoe2", "actions": "/", "secrets": "test_secret1"})
        bandicoot.cli.api.db.roles.insert_one({"name": "test_role2", "users": "jdoe3", "actions": "/testing", "secrets": "test_secret2"})

        bandicoot.cli.api.db.secrets.insert_one({"name": "deleteme", "secret": "foundme1"})
        bandicoot.cli.api.db.secrets.insert_one({"name": "test_secret1", "secret": "foundme1"})
        bandicoot.cli.api.db.secrets.insert_one({"name": "test_secret2", "secret": "foundme2"})

    def test_plugin_help_unprivuser(self):
        result = builtins.plugin_help("jdoe3", {"category": "/", "actions": "help"}, {})
        assert("exit" in result)

    def test_plugin_help_privuser(self):
        result = builtins.plugin_help("jdoe2", {"category": "/", "actions": "help"}, {})
        assert("exit" in result)

    def test_plugin_ping(self):
        result = builtins.plugin_ping("jdoe3", {}, {})
        assert(result == json.dumps({"exit_code": 0, "response": "  pong"}))

    def test_plugin_users_del_name_missing(self):
        result = builtins.plugin_users_del("jdoe3", {}, {})
        assert(result == json.dumps({"exit_code": 1, "response": "  username option is required"}))

    def test_plugin_users_del_does_not_exist(self):
        result = builtins.plugin_users_del("jdoe3", {}, {"username": "user_nomatch"})
        assert(result == json.dumps({"exit_code": 1, "response": "  user user_nomatch does not exist"}))

    def test_plugin_users_del(self):
        result = builtins.plugin_users_del("jdoe3", {}, {"username": "deleteme"})
        assert(result == json.dumps({"exit_code": 0, "response": "  deleted user deleteme"}))

    def test_plugin_users_add(self):
        result = builtins.plugin_users_add("jdoe3", None, {"username": "add_test", "password": "a"})
        assert (result == json.dumps({"exit_code": 0, "response": "  created user add_test"}))

    def test_plugin_users_add_options_supported(self):
        result = builtins.plugin_users_add("jdoe3", None, {"unsupported_option": "unsupported","username": "add_test", "password": "a"})
        assert ( json.loads(result)["exit_code"] == 1 )

    def test_plugin_users_add_already_exists(self):
        result = builtins.plugin_users_add(None, None, {"username": "jdoe1", "password": "a"})
        assert (result == json.dumps({"exit_code": 1, "response": "  user jdoe1 already exists"}))

    def test_plugin_users_add_name_missing(self):
        result_uonly = builtins.plugin_users_add(None, None, {"username": "jdoe"})
        result_ponly = builtins.plugin_users_add(None, None, {"password": "jdoe"})
        assert(result_uonly == json.dumps({"exit_code": 1, "response": "  password option is required"})
            and result_ponly == json.dumps({"exit_code": 1, "response": "  username option is required"}))

    def test_plugin_users_edit_passwd_missing(self):
        result = builtins.plugin_users_edit(None, None, {"username": "a"})
        assert (result == json.dumps({"exit_code": 1, "response": "  password option is required"}))

    def test_plugin_users_edit_nouser(self):
        result = builtins.plugin_users_edit(None, None, {"username": "no_user", "password": "newpw"})
        assert (result == json.dumps({"exit_code": 1, "response": "  user no_user does not exist"}))

    def test_plugin_users_edit(self):
        result = builtins.plugin_users_edit(None, None, {"username": "jdoe2", "password": "newpw"})
        assert (result == json.dumps({"exit_code": 0, "response": "  modified user jdoe2"}))

    def test_plugin_users_edit_nousername(self):
        result = builtins.plugin_users_edit("jdoe2", None, {"password": "newpw"})
        print(result)
        assert (result == json.dumps({"exit_code": 0, "response": "  modified user jdoe2"}))

    def test_plugin_users_list(self):
        result = builtins.plugin_users_list(None, None, {})
        assert (result == json.dumps({"exit_code": 0, "response": "  jdoe1\n  jdoe2\n  jdoe3\n  jdoe4\n  add_test"}))

    def test_plugin_actions_add_invalid_char(self):
        result = builtins.plugin_actions_add(None, None, {"name": "test", "desc": "test", "plugin": "command", "action": "test", "category": "/$$$"})
        print(result)
        assert(result == json.dumps({"exit_code": 1, "response": "  option category=/$$$ has invalid characters"}))

    def test_plugin_actions_add_category_fix_trailing_slash(self):
        result = builtins.plugin_actions_add(None, None, {"name": "test_slash_action1", "category": "/fixtest1/", "action": "test", "plugin": "command", "desc": "test"})
        action_list = json.loads(builtins.plugin_actions_list(None, None, {}))
        category_format_correct = False
        for line in action_list["response"].split("\n"):
            if 'category="/fixtest1"':
                category_format_correct = True
        builtins.plugin_actions_del(None, None, {"name": "test_slash_action1"})
        assert(result == json.dumps({"exit_code": 0, "response": "  created action test_slash_action1"}) and category_format_correct == True)

    def test_plugin_actions_add_category_fix_no_prepended_slash(self):
        result = builtins.plugin_actions_add(None, None, {"name": "test_slash_action2", "category": "fixtest2", "action": "test", "plugin": "command", "desc": "test"})
        action_list = json.loads(builtins.plugin_actions_list(None, None, {}))
        category_format_correct = False
        for line in action_list["response"].split("\n"):
            if 'category="/fixtest2"':
                category_format_correct = True
        builtins.plugin_actions_del(None, None, {"name": "test_slash_action2"})
        assert(result == json.dumps({"exit_code": 0, "response": "  created action test_slash_action2"}) and category_format_correct == True)

    def test_plugin_actions_add_name_missing(self):
        result = builtins.plugin_actions_add(None, None, {"category": "/"})
        assert(result == json.dumps({"exit_code": 1, "response": "  name option is required"}))

    def test_plugin_actions_add_category_missing(self):
        result = builtins.plugin_actions_add(None, None, {"name": "jaction"})
        assert(result == json.dumps({"exit_code": 1, "response": "  category option is required"}))

    def test_plugin_actions_add_action_missing(self):
        result = builtins.plugin_actions_add(None, None, {"name": "jaction", "category": "/"})
        assert(result == json.dumps({"exit_code": 1, "response": "  action option is required"}))

    def test_plugin_actions_add_plugin_missing(self):
        result = builtins.plugin_actions_add(None, None, {"name": "jaction", "category": "/", "action": "test"})
        assert(result == json.dumps({"exit_code": 1, "response": "  plugin option is required"}))

    def test_plugin_actions_add_disc_missing(self):
        result = builtins.plugin_actions_add(None, None, {"name": "jaction", "category": "/", "action": "test", "plugin": "command"})
        assert(result == json.dumps({"exit_code": 1, "response": "  desc option is required"}))

    def test_plugin_actions_add_already_exists(self):
        result = builtins.plugin_actions_add(None, None, {"name": "test_action1", "category": "/", "action": "test", "plugin": "command", "desc": "test"})
        assert(result == json.dumps({"exit_code": 1, "response": "  action test_action1 already exists"}))

    def test_plugin_actions_add(self):
        result = builtins.plugin_actions_add(None, None, {"name": "add_test", "category": "/", "action": "test", "plugin": "command", "desc": "test"})
        assert(result == json.dumps({"exit_code": 0, "response": "  created action add_test"}))

    def test_plugin_actions_del_name_missing(self):
        result = builtins.plugin_actions_del(None, None, {})
        assert(result == json.dumps({"exit_code": 1, "response": "  name option is required"}))

    def test_plugin_actions_del_noaction(self):
        result = builtins.plugin_actions_del(None, None, {"name": "noaction"})
        assert(result == json.dumps({"exit_code": 1, "response": "  action noaction does not exist"}))

    def test_plugin_actions_del(self):
        result = builtins.plugin_actions_del(None, None, {"name": "deleteme"})
        assert(result == json.dumps({"exit_code": 0, "response": "  deleted action deleteme"}))

    def test_plugin_actions_edit_name_missing(self):
        result = builtins.plugin_actions_edit(None, None, {})
        assert(result == json.dumps({"exit_code": 1, "response": "  name option is required"}))

    def test_plugin_actions_edit_noaction(self):
        result = builtins.plugin_actions_edit(None, None, {"name": "noaction"})
        assert(result == json.dumps({"exit_code": 1, "response": "  action noaction does not exist"}))

    def test_plugin_actions_edit(self):
        result = builtins.plugin_actions_edit(None, None, {"name": "test_action1"})
        assert(result == json.dumps({"exit_code": 0, "response": "  modified action test_action1"}))

    def test_plugin_actions_list(self):
        result = builtins.plugin_actions_list(None, None, {})
        assert (result == json.dumps({"exit_code": 0, "response": "  action=\"pwd\"   category=\"/testing\"   command_run=\"echo 'hello world'\"   desc=\"test pwd\"   name=\"test_action1\"   plugin=\"command\" \n  action=\"ls\"   category=\"/testing\"   command_run=\"echo 'hello world'\"   desc=\"test ls\"   name=\"test_action2\"   plugin=\"command\" \n  action=\"test\"   category=\"/\"   desc=\"test\"   name=\"add_test\"   plugin=\"command\""}) )

    def test_plugin_roles_add_name_missing(self):
        result = builtins.plugin_roles_add(None, None, {})
        assert(result == json.dumps({"exit_code": 1, "response": "  name option is required"}))

    def test_plugin_roles_add_already_exists(self):
        result = builtins.plugin_roles_add(None, None, {"name": "test_role1"})
        assert(result == json.dumps({"exit_code": 1, "response": "  role test_role1 already exists"}))

    def test_plugin_roles_add(self):
        result = builtins.plugin_roles_add(None, None, {"name": "add_test"})
        assert(result == json.dumps({"exit_code": 0, "response": "  created role add_test"}))

    def test_plugin_roles_del_name_missing(self):
        result = builtins.plugin_roles_del(None, None, {})
        assert(result == json.dumps({"exit_code": 1, "response": "  name option is required"}))

    def test_plugin_roles_del_noaction(self):
        result = builtins.plugin_roles_del(None, None, {"name": "noaction"})
        assert(result == json.dumps({"exit_code": 1, "response": "  role noaction does not exist"}))

    def test_plugin_roles_del(self):
        result = builtins.plugin_roles_del(None, None, {"name": "deleteme"})
        assert(result == json.dumps({"exit_code": 0, "response": "  deleted role deleteme"}))

    def test_plugin_roles_edit_name_missing(self):
        result = builtins.plugin_roles_edit(None, None, {})
        assert(result == json.dumps({"exit_code": 1, "response": "  name option is required"}))

    def test_plugin_roles_edit_noaction(self):
        result = builtins.plugin_roles_edit(None, None, {"name": "norole"})
        assert(result == json.dumps({"exit_code": 1, "response": "  role norole does not exist"}))

    def test_plugin_roles_edit(self):
        result = builtins.plugin_roles_edit(None, None, {"name": "test_role1"})
        assert(result == json.dumps({"exit_code": 0, "response": "  modified role test_role1"}))

    def test_plugin_roles_list(self):
        result = builtins.plugin_roles_list(None, None, {})
        assert (result == json.dumps({"exit_code": 0, "response": "  actions=\"/\"   name=\"test_role1\"   secrets=\"test_secret1\"   users=\"jdoe2\" \n  actions=\"/testing\"   name=\"test_role2\"   secrets=\"test_secret2\"   users=\"jdoe3\" \n  name=\"add_test\""}) )

    def test_plugin_secrets_add_name_missing(self):
        result = builtins.plugin_secrets_add(None, None, {})
        assert(result == json.dumps({"exit_code": 1, "response": "  name option is required"}))

    def test_plugin_secrets_add_already_exists(self):
        result = builtins.plugin_secrets_add(None, None, {"name": "test_secret1"})
        assert(result == json.dumps({"exit_code": 1, "response": "  secret test_secret1 already exists"}))

    def test_plugin_secrets_add(self):
        result = builtins.plugin_secrets_add(None, None, {"name": "add_test"})
        assert(result == json.dumps({"exit_code": 0, "response": "  created secret add_test"}))

    def test_plugin_secrets_del_name_missing(self):
        result = builtins.plugin_secrets_del(None, None, {})
        assert(result == json.dumps({"exit_code": 1, "response": "  name option is required"}))

    def test_plugin_secrets_del_noaction(self):
        result = builtins.plugin_secrets_del(None, None, {"name": "noaction"})
        assert(result == json.dumps({"exit_code": 1, "response": "  secret noaction does not exist"}))

    def test_plugin_secrets_del(self):
        result = builtins.plugin_secrets_del(None, None, {"name": "deleteme"})
        assert(result == json.dumps({"exit_code": 0, "response": "  deleted secret deleteme"}))

    def test_plugin_secrets_edit_name_missing(self):
        result = builtins.plugin_secrets_edit(None, None, {})
        assert(result == json.dumps({"exit_code": 1, "response": "  name option is required"}))

    def test_plugin_secrets_edit_noaction(self):
        result = builtins.plugin_secrets_edit(None, None, {"name": "nosecret"})
        assert(result == json.dumps({"exit_code": 1, "response": "  secret nosecret does not exist"}))

    def test_plugin_secrets_edit(self):
        result = builtins.plugin_secrets_edit(None, None, {"name": "test_secret1"})
        assert(result == json.dumps({"exit_code": 0, "response": "  modified secret test_secret1"}))

    def test_plugin_secrets_list(self):
        result = builtins.plugin_secrets_list(None, None, {})
        print(result)
        assert (result == json.dumps({"exit_code": 0, "response": "  name=\"test_secret1\"   secret=\"...\"   status=\"cleartext\" \n  name=\"test_secret2\"   secret=\"...\"   status=\"cleartext\" \n  name=\"add_test\""}) )

    def test_plugin_command_commandrun_missing(self):
        result = builtins.plugin_command(None, {}, {})
        assert(result == json.dumps({"exit_code": 1, "response": "  command_run required in action"}))

    def test_plugin_command(self):
        result = builtins.plugin_command(None, {"command_run": "echo 'hello world'"}, {})
        assert(result == json.dumps({"exit_code": 0, "response": "  'hello world'\n\n  return code: 0\n"}))

    def test_plugin_plugins_list(self):
        result = builtins.plugin_plugins_list(None, {}, {})
        resp_list = [x.encode("UTF8") for x in json.loads(result)["response"].split()]
        map(str.strip, resp_list)
        assert( "actions_list" in resp_list and "roles_list" in resp_list)

    def test_plugin_logs(self):
        result = builtins.plugin_logs(None, {}, {})
        print(result)
        assert(result == json.dumps({"exit_code": 0, "response": "  category\t\taction\t\toptions\t\tdate\n"}))

    def test_plugin_logs_backwardcompat(self):
        post = {}
        post["category"] = "/testing"
        post["action"] = {"name": "testaction"}
        post["options"] = {"testopt": "something"}
        # Missing Attributes in older version of bandicoot, test backward compat
        # post["result"]
        # post["date"]
        # post["user"]
        bandicoot.cli.api.db.logs.insert_one(post)
        result = builtins.plugin_logs(None, {}, {})
        print(result)
        assert(result == json.dumps({"exit_code": 0, "response": "  category\t\taction\t\toptions\t\tdate\n  unknown\t/testing\t{'name': 'testaction'}\t{'testopt': 'something'}\t01/01/1970 00:00\n"}))

    def test_plugin_jobs_status_id_required(self):
        result = builtins.plugin_jobs_status(None, {}, {})
        print(result)
        assert(result == json.dumps({"exit_code": 1, "response": "  id option is required"}))

    def test_plugin_jobs_status_id_not_found(self):
        result = builtins.plugin_jobs_status(None, {}, {"id": "100"})
        print(result)
        assert(result == json.dumps({"exit_code": 1, "response": "  The job id 100 does not match a job", "exit_code": 1}))

    def test_plugin_jobs_status_wronguser(self):
        result = builtins.plugin_jobs_status("joesmoe1", {}, {"id": "1"})
        print(result)
        assert(result == json.dumps({"exit_code": 1, "response": "  The job 1, is owned by another user", "exit_code": 1}))

    def test_plugin_jobs_status(self):
        result = builtins.plugin_jobs_status("joesmoe", {}, {"id": "1"})
        print(result)
        assert(result == json.dumps({"finished": True, "response": "", "exit_code": 0}))

    def test_plugin_jobs_list(self):
        result = json.loads(builtins.plugin_jobs_list(None, {}, {}))
        number_of_jobs = len(result["response"].split("\n"))
        assert(number_of_jobs == 3)

    def test_plugin_jobs_kill_id_required(self):
        result = builtins.plugin_jobs_kill(None, {}, {})
        print(result)
        assert(result == json.dumps({"exit_code": 1, "response": "  id option is required"}))

    def test_plugin_jobs_kill_id_not_found(self):
        result = builtins.plugin_jobs_kill(None, {}, {"id": "100"})
        print(result)
        assert(result == json.dumps({"exit_code": 1, "response": "  The job id 100 does not match a job"}))

    def test_plugin_jobs_kill(self):
        result = builtins.plugin_jobs_kill("joesmoe", {}, {"id": "1"})
        print(result)
        assert(result == json.dumps({"exit_code": 0, "response": "  The job 1, was terminated"}))

    def test_plugin_jobs_kill_alreadyterminated(self):
        result = builtins.plugin_jobs_kill("joesmoe", {}, {"id": "1"})
        print(result)
        assert(result == json.dumps({"exit_code": 1, "response": "  The job 1, was already terminated"}))

#    def test_plugin_jobs_kill_wronguser(self):
#        result = builtins.plugin_jobs_kill("joesmoe", {}, {"id": 1})
#        print(result)
#        assert(result == json.dumps({"exit_code": 1, "response": "  The job 1, is owned by another user"}))

    @mock.patch('subprocess.Popen', return_value=MockPopen([], []))
    def test_plugin_ansible_withdecorator(self, mock_popen):
        result = builtins.plugin_ansible("joesmoe", {"action": "test", "category": "/", "source_url": "git://test", "playbook": "test.yml", "sudo": False}, {})
        assert("queue_id" in json.loads(result))

    @mock.patch('sys.exit', return_value=0) # do not really exit, as if it were really a thread
    @mock.patch('subprocess.Popen', return_value=MockPopen([], []))
    def test_plugin_ansible_source_url_required(self, mock_exit, mock_popen):
        q = multiprocessing.Queue()
        result = builtins.plugin_ansible._original(None, {"action": "test", "category": "/"}, {}, multiprocessing.Event(), q)
        assert(result == json.dumps({"exit_code": 1, "response": "  source_url required in action"}))

    @mock.patch('sys.exit', return_value=0) # do not really exit, as if it were really a thread
    @mock.patch('subprocess.Popen', return_value=MockPopen([], []))
    def test_plugin_ansible_playbook_required(self, mock_exit, mock_popen):
        q = multiprocessing.Queue()
        result = builtins.plugin_ansible._original(None, {"action": "test", "category": "/", "source_url": "git://test"}, {}, multiprocessing.Event(), q)
        assert(result == json.dumps({"exit_code": 1, "response": "  playbook required in action"}))

    @mock.patch('sys.exit', return_value=0) # do not really exit, as if it were really a thread
    @mock.patch('subprocess.Popen', return_value=MockPopen([], []))
    def test_plugin_ansible_usingsudo(self, mock_exit, mock_popen):
        q = multiprocessing.Queue()
        result = builtins.plugin_ansible._original(None, {"action": "test", "category": "/", "source_url": "git://test", "playbook": "test.yml", "sudo": "yes"}, {}, multiprocessing.Event(), q)
        assert(result == json.dumps({"exit_code": 0, "response": "  success"}))

    @mock.patch('sys.exit', return_value=0) # do not really exit, as if it were really a thread
    @mock.patch('subprocess.Popen', return_value=MockPopen([], []))
    def test_plugin_ansible_nodecorator(self, mock_exit, mock_popen):
        q = multiprocessing.Queue()
        result = builtins.plugin_ansible._original(None, {"action": "test", "category": "/", "source_url": "git://test", "playbook": "test.yml", "sudo": "no"}, {}, multiprocessing.Event(), q)
        assert(result == json.dumps({"exit_code": 0, "response": "  success"}))

    def test_plugin_schedules_add(self):
        result = builtins.plugin_schedules_add(None, None, {"name": "add_test", "category": "/", "action": "help"})
        assert(result == json.dumps({"exit_code": 0, "response": "  created schedule add_test"}))

    def test_plugin_schedules_add_usernone(self):
        result = builtins.plugin_schedules_add(None, None, {"name": "add_test_usernone", "category": "/", "action": "help"})
        assert(result == json.dumps({"exit_code": 0, "response": "  created schedule add_test_usernone"}))

    def test_plugin_schedules_add_duplicatename(self):
        result = builtins.plugin_schedules_add(None, None, {"name": "add_test", "category": "/", "action": "help"})
        assert(result == json.dumps({"exit_code": 1, "response": "  schedule add_test already exists"}))

    def test_plugin_schedules_add_forgingrequest(self):
        result = builtins.plugin_schedules_add("forgeuser", None, {"user": "jdoe2", "name": "add_test_forge", "category": "/", "action": "help"})
        print(result)
        assert(result == json.dumps({"exit_code": 1, "response": "  You cannot set the cron user to anyone but your username forgeuser."}))

    def test_plugin_schedules_edit(self):
        result = builtins.plugin_schedules_edit(None, None, {"name": "add_test_usernone", "category": "/", "action": "help"})
        print(result)
        assert(result == json.dumps({"exit_code": 0, "response": "  modified schedule add_test_usernone"}))

    def test_plugin_schedules_edit_noexist(self):
        result = builtins.plugin_schedules_edit(None, None, {"name": "doesnotexist", "category": "/", "action": "help"})
        print(result)
        assert(result == json.dumps({"exit_code": 1, "response": "  schedule doesnotexist does not exist"}))

    def test_plugin_schedules_edit_forgingrequest(self):
        result = builtins.plugin_schedules_edit("forgeuser", None, {"user": "jdoe3", "name": "add_test_usernone", "category": "/", "action": "help"})
        print(result)
        assert(result == json.dumps({"exit_code": 1, "response": "  You cannot set the cron user to anyone but your username forgeuser."}))

    def test_plugin_schedules_del(self):
        result = builtins.plugin_schedules_del(None, None, {"name": "add_test"})
        print(result)
        assert(result == json.dumps({"exit_code": 0, "response": "  deleted schedule add_test"}))

    def test_plugin_schedules_del_doesnotexist(self):
        result = builtins.plugin_schedules_del(None, None, {"name": "does_not_exist"})
        print(result)
        assert(result == json.dumps({"exit_code": 1, "response": "  schedule does_not_exist does not exist"}))

    def test_plugin_schedules_list(self):
        result = builtins.plugin_schedules_list(None, None, {})
        print(result)
        assert(result == json.dumps({"exit_code": 0, "response": "  action=\"help\"   category=\"/\"   name=\"add_test_usernone\"   user=\"None\""}))

    def test_plugin_inventory_list(self):
        result = builtins.plugin_inventory_list(None, None, {})
        print(result)
        assert(result == json.dumps({"exit_code": 0, "response": ""}))

    def test_plugin_inventory_del_doesnotexist(self):
        result = builtins.plugin_inventory_del(None, None, {"name": "doesnotexist"})
        print(result)
        assert(result == json.dumps({"exit_code": 1, "response": "  inventory item doesnotexist does not exist"}))

    def test_plugin_stats(self):
        result = builtins.plugin_stats(None, None, {})
        print(result)
        assert(u"Jobs Submitted Per User" in json.loads(result)["response"])

    def test_plugin_stats_users(self):
        result = builtins.plugin_stats(None, None, {"type": "users"})
        print(result)
        assert(u"Jobs Submitted Per User" in json.loads(result)["response"])

    def test_plugin_stats_system(self):
        result = builtins.plugin_stats(None, None, {"type": "system"})
        print(result)
        assert(u"Changes Per Inventory Item" in json.loads(result)["response"])

    def test_plugin_stats_jobs(self):
        result = builtins.plugin_stats(None, None, {"type": "jobs"})
        print(result)
        assert(u"Jobs Submitted By Date" in json.loads(result)["response"])

    def test_plugin_stats_badtype(self):
        result = builtins.plugin_stats(None, None, {"type": "abcdefg"})
        print(result)
        assert(u"Jobs Submitted Per User" in json.loads(result)["response"])
