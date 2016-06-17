import nose
import outbit
from outbit.plugins import builtins
import unittest
import json
import mock
import mongomock
import outbit.cli.api


class TestCli(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        self.mock_db_setup()
        self.mock_db_basic_database()
        unittest.TestCase.__init__(self, *args, **kwargs)

    def mock_db_setup(self):
        outbit.cli.api.dbclient = mongomock.MongoClient()
        outbit.cli.api.db = outbit.cli.api.dbclient.conn["outbit"]

    def mock_db_basic_database(self):
        outbit.cli.api.db.users.insert_one({"username": "jdoe1", "password_md5": "md5test"})
        outbit.cli.api.db.users.insert_one({"username": "jdoe2", "password_md5": "md5test"})
        outbit.cli.api.db.users.insert_one({"username": "jdoe3", "password_md5": "md5test"})
        outbit.cli.api.db.users.insert_one({"username": "jdoe4", "password_md5": "md5test"})
        outbit.cli.api.db.actions.insert_one({"name": "test_action1", "category": "/testing", "action": "pwd", "plugin": "command", "command_run": "echo 'hello world'", "desc": "test pwd"})
        outbit.cli.api.db.actions.insert_one({"name": "test_action2", "category": "/testing", "action": "ls", "plugin": "command", "command_run": "echo 'hello world'", "desc": "test ls"})
        outbit.cli.api.db.roles.insert_one({"name": "test_role1", "users": "jdoe2", "category": "/", "secrets": "test_secret1"})
        outbit.cli.api.db.roles.insert_one({"name": "test_role2", "users": "jdoe3", "category": "/testing", "secrets": "test_secret2"})
        outbit.cli.api.db.secrets.insert_one({"name": "test_secret1", "secret": "foundme1"})
        outbit.cli.api.db.secrets.insert_one({"name": "test_secret2", "secret": "foundme2"})

    @mock.patch("outbit.cli.api.db")
    def test_plugin_help(self, mock_test):
        result = builtins.plugin_help("jdoe3", {}, {})
        assert("exit" in result)

    def test_plugin_ping(self):
        result = builtins.plugin_ping("jdoe3", {}, {})
        assert(result == json.dumps({"response": "  pong"}))

    def test_plugin_users_del_name_missing(self):
        result = builtins.plugin_users_del("jdoe3", {}, {})
        assert(result == json.dumps({"response": "  username option is required"}))

    def test_plugin_users_del_does_not_exist(self):
        result = builtins.plugin_users_del("jdoe3", {}, {"username": "user_nomatch"})
        assert(result == json.dumps({"response": "  user user_nomatch does not exist"}))

    def test_plugin_users_del(self):
        result = builtins.plugin_users_del("jdoe3", {}, {"username": "jdoe1"})
        assert(result == json.dumps({"response": "  deleted user jdoe1"}))

    def test_plugin_users_add(self):
        result = builtins.plugin_users_add("jdoe3", None, {"username": "add_test", "password": "a"})
        print(result)
        assert (result == json.dumps({"response": "  created user add_test"}))

    def test_plugin_users_add_already_exists(self):
        result = builtins.plugin_users_add(None, None, {"username": "jdoe1", "password": "a"})
        assert (result == json.dumps({"response": "  user jdoe1 already exists"}))

    def test_plugin_users_add_name_missing(self):
        result_uonly = builtins.plugin_users_add(None, None, {"username": "jdoe"})
        result_ponly = builtins.plugin_users_add(None, None, {"password": "jdoe"})
        assert(result_uonly == json.dumps({"response": "  username and password are required options"})
            and result_ponly == json.dumps({"response": "  username and password are required options"}))

    def test_plugin_actions_add_name_missing(self):
        result = builtins.plugin_actions_add(None, None, {"category": "/"})
        assert(result == json.dumps({"response": "  name option is required"}))

    def test_plugin_actions_add_category_missing(self):
        result = builtins.plugin_actions_add(None, None, {"name": "jaction"})
        assert(result == json.dumps({"response": "  category option is required"}))

    def test_plugin_actions_add_action_missing(self):
        result = builtins.plugin_actions_add(None, None, {"name": "jaction", "category": "/"})
        assert(result == json.dumps({"response": "  action option is required"}))

    def test_plugin_actions_add_plugin_missing(self):
        result = builtins.plugin_actions_add(None, None, {"name": "jaction", "category": "/", "action": "test"})
        assert(result == json.dumps({"response": "  plugin option is required"}))

    def test_plugin_actions_del(self):
        result = builtins.plugin_actions_del(None, None, {})
        assert(result == json.dumps({"response": "  name option is required"}))

    def test_plugin_roles_add(self):
        result = builtins.plugin_roles_add(None, None, {})
        assert(result == json.dumps({"response": "  name option is required"}))

    def test_plugin_roles_del(self):
        result = builtins.plugin_roles_del(None, None, {})
        assert(result == json.dumps({"response": "  name option is required"}))