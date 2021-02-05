import nose
from bandicoot.parser import yacc
import unittest
import sys
import os

class TestCli(unittest.TestCase):
    def test_lexskip(self):
        yacc.parser.parse("help?'")
        # skip characters not known
        assert(yacc.parser_category == "/" and yacc.parser_action == "help")

    def test_parseerror_eof(self):
        yacc.parser.parse("=")
        # action is missing
        assert(yacc.parser_error == "Syntax error at EOF")

    def test_parseerror_line(self):
        yacc.parser.parse("help=something list=something")
        # action is missing
        assert(yacc.parser_error == "Syntax error at character: 'something', column: 5")

    def test_parser_quoted_var_single(self):
        yacc.parser.parse("users del username='something'")
        # action is missing
        assert(yacc.parser_category == "/users" and yacc.parser_action == "del"
                and yacc.parser_options["username"] == "something")

    def test_parser_quoted_var_double(self):
        yacc.parser.parse('users del username="something"')
        # action is missing
        assert(yacc.parser_category == "/users" and yacc.parser_action == "del"
                and yacc.parser_options["username"] == "something")

    def test_parser_category_and_action(self):
        yacc.parser.parse('testing this users del username="something"')
        # action is missing
        assert(yacc.parser_category == "/testing/this/users" and yacc.parser_action == "del"
                and yacc.parser_options["username"] == "something")

    def test_parser_actiononly(self):
        yacc.parser.parse("help")
        # action is missing
        assert(yacc.parser_category == "/" and yacc.parser_action == "help")

    def test_p_action_run_help(self):
        t = []
        t.append(None)
        t.append(["help",])
        yacc.p_action_run(t)
        assert(yacc.parser_category == "/" and yacc.parser_action == "help")

    def test_p_action_run_users_list(self):
        t = []
        t.append(None)
        t.append(["users","list"])
        yacc.p_action_run(t)
        assert(yacc.parser_category == "/users" and yacc.parser_action == "list")

    def test_p_action_run_users_del(self):
        t = []
        t.append(None)
        t.append(["users","del"])
        t.append(" ")
        t.append({"username": "jdoe"})
        yacc.p_action_run(t)
        assert(yacc.parser_category == "/users" and yacc.parser_action == "del" and "username" in yacc.parser_options)

    def test_p_actions_str(self):
        t = []
        t.append(None)
        t.append("help")
        yacc.p_actions(t)
        assert(t[0] == ["help"])

    def test_p_actions_list(self):
        t = []
        t.append(None)
        t.append(["users"])
        t.append(" ")
        t.append("list")
        yacc.p_actions(t)
        assert(t[0] == ["users", "list"])

    def test_p_actions_singleaction(self):
        t = []
        t.append(None)
        t.append("users")
        t.append(" ")
        t.append("list")
        yacc.p_actions(t)
        assert(t[0] == ["users", "list"])

    def test_p_options_1(self):
        t = []
        t.append(None)
        t.append({"username": "jdoe"})
        yacc.p_options(t)
        assert(t[0] == {"username": "jdoe"})

    def test_p_options_2(self):
        t = []
        t.append(None)
        t.append({"username": "jdoe"})
        t.append(" ")
        t.append({"password": "jdoe"})
        yacc.p_options(t)
        assert(t[0] == {"username": "jdoe", "password": "jdoe"})

    def test_p_option(self):
        t = []
        t.append(None)
        t.append("username")
        t.append("=")
        t.append("jdoe")
        yacc.p_option(t)
        assert(t[0] == {"username": "jdoe"})
