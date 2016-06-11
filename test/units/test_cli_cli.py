import nose
from outbit.cli import cli as cli
import unittest
import sys
import os

class TestCli(unittest.TestCase):
    def test_p_action_run_help(self):
        t = []
        t.append(None)
        t.append(["help",])
        cli.p_action_run(t)
        assert(cli.parser_category == "/" and cli.parser_action == "help")

    def test_p_action_run_users_list(self):
        t = []
        t.append(None)
        t.append(["users","list"])
        cli.p_action_run(t)
        assert(cli.parser_category == "/users" and cli.parser_action == "list")

    def test_p_action_run_users_del(self):
        t = []
        t.append(None)
        t.append(["users","del"])
        t.append(" ")
        t.append({"username": "jdoe"})
        cli.p_action_run(t)
        assert(cli.parser_category == "/users" and cli.parser_action == "del" and "username" in cli.parser_options)

    def test_p_actions_str(self):
        t = []
        t.append(None)
        t.append("help")
        cli.p_actions(t)
        assert(t[0] == ["help"])

    def test_p_actions_list(self):
        t = []
        t.append(None)
        t.append(["users"])
        t.append(" ")
        t.append("list")
        cli.p_actions(t)
        print(t)
        assert(t[0] == ["users", "list"])

    def test_p_options_1(self):
        t = []
        t.append(None)
        t.append({"username": "jdoe"})
        cli.p_options(t)
        assert(t[0] == {"username": "jdoe"})

    def test_p_options_2(self):
        t = []
        t.append(None)
        t.append({"username": "jdoe"})
        t.append(" ")
        t.append({"password": "jdoe"})
        cli.p_options(t)
        assert(t[0] == {"username": "jdoe", "password": "jdoe"})

    def test_project(self):
        # Test No Path Given (Hello Test)
        sys.argv[1] = ""
        sys.argv[2] = ""
        cliobj = cli.Cli()
        assert(cliobj is not None)
