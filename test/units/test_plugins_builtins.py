import nose
import outbit
from outbit.plugins import builtins
import unittest
import json
import mock


class TestCli(unittest.TestCase):
    @mock.patch("outbit.cli.api.db")
    def test_plugin_help(self, mock_test):
        tester = mock.Mock()
        mock_test.return_value = tester
        result = builtins.plugin_help(None, None)
        assert("users list" in result)

    def test_plugin_ping(self):
        result = builtins.plugin_ping(None, None)
        assert(result == json.dumps({"response": "  pong"}))

    def test_plugin_users_del(self):
        result = builtins.plugin_users_del(None, {})
        assert(result == json.dumps({"response": "  name option is required"}))

    def test_plugin_users_add(self):
        result_uonly = builtins.plugin_users_add(None, {"username": "jdoe"})
        result_ponly = builtins.plugin_users_add(None, {"password": "jdoe"})
        assert(result_uonly == json.dumps({"response": "  username and password are required options"})
            and result_ponly == json.dumps({"response": "  username and password are required options"}))

    def test_plugin_actions_add_name_missing(self):
        result = builtins.plugin_actions_add(None, {"category": "/"})
        assert(result == json.dumps({"response": "  name option is required"}))

    def test_plugin_actions_add_category_missing(self):
        result = builtins.plugin_actions_add(None, {"name": "jaction"})
        assert(result == json.dumps({"response": "  category option is required"}))

    def test_plugin_actions_add_action_missing(self):
        result = builtins.plugin_actions_add(None, {"name": "jaction", "category": "/"})
        assert(result == json.dumps({"response": "  action option is required"}))

    def test_plugin_actions_add_plugin_missing(self):
        result = builtins.plugin_actions_add(None, {"name": "jaction", "category": "/", "action": "test"})
        assert(result == json.dumps({"response": "  plugin option is required"}))

    def test_plugin_actions_del(self):
        result = builtins.plugin_actions_del(None, {})
        assert(result == json.dumps({"response": "  name option is required"}))

    def test_plugin_roles_add(self):
        result = builtins.plugin_roles_add(None, {})
        assert(result == json.dumps({"response": "  name option is required"}))

    def test_plugin_roles_del(self):
        result = builtins.plugin_roles_del(None, {})
        assert(result == json.dumps({"response": "  name option is required"}))