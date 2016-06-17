import nose
import outbit
from outbit.plugins import builtins
import unittest
import json
import mock
import mongomock
import outbit.cli.api


class TestCli(unittest.TestCase):
    def mock_db_setup(self):
        if outbit.cli.api.dbclient is None and outbit.cli.api.db is None:
            outbit.cli.api.dbclient = mongomock.Connection()
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
        self.mock_db_setup()
        self.mock_db_basic_database()
        result = builtins.plugin_help("jdoe3", {}, {})
        assert("exit" in result)

    def test_plugin_ping(self):
        self.mock_db_setup()
        self.mock_db_basic_database()
        result = builtins.plugin_ping("jdoe3", {}, {})
        assert(result == json.dumps({"response": "  pong"}))

    def test_plugin_users_del_name_missing(self):
        result = builtins.plugin_users_del("jdoe3", {}, {})
        assert(result == json.dumps({"response": "  username option is required"}))

    def test_plugin_users_del(self):
        self.mock_db_setup()
        self.mock_db_basic_database()
        result = builtins.plugin_users_del("jdoe3", {}, {"username": "jdoe1"})
        assert(result == json.dumps({"response": "  deleted user jdoe1"}))

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