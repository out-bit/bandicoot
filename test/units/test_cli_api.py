import nose
from outbit.cli import api
import unittest
import sys
import os
import json

class TestCli(unittest.TestCase):
    def test_plugin_ping(self):
        result = api.plugin_ping(None, None)
        assert(result == json.dumps({"response": "  pong"}))

    def test_plugin_users_add(self):
        result_uonly = api.plugin_users_add(None, {"username": "jdoe"})
        result_ponly = api.plugin_users_add(None, {"password": "jdoe"})
        assert(result_uonly == json.dumps({"response": "  username and password are required options"})
            and result_ponly == json.dumps({"response": "  username and password are required options"}))

    def test_project(self):
        # Test No Path Given (Hello Test)
        sys.argv[1] = ""
        sys.argv[2] = ""
        cli = api.Cli()
        assert(cli is not None)
