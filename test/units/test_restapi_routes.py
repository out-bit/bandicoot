import nose
import unittest
from bandicoot.cli import api
from bandicoot.restapi import routes
import mongomock
from flask import Response


class TestCli(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        self.mock_db_setup()
        self.mock_db_basic_database()
        unittest.TestCase.__init__(self, *args, **kwargs)

    def mock_db_setup(self):
        api.dbclient = mongomock.MongoClient()
        api.db = api.dbclient.conn["bandicoot"]

    def mock_db_basic_database(self):
        api.db.users.insert_one({"username": "jdoe1", "password_md5": "5f4dcc3b5aa765d61d8327deb882cf99"})

        api.db.actions.insert_one({"name": "test_action1", "category": "/testing", "action": "pwd", "plugin": "command", "command_run": "echo 'hello world'", "desc": "test pwd"})

        api.db.roles.insert_one({"name": "test_role1", "users": "jdoe2", "actions": "/", "secrets": "test_secret1"})

        api.db.secrets.insert_one({"name": "test_secret1", "secret": "foundme1"})

    def test_check_auth_fail(self):
        assert( routes.check_auth("jdoe1", "wrongpw") == False )

    def test_check_auth(self):
        assert( routes.check_auth("jdoe1", "password") == True )

    def test_rest_request_is_valid_empty(self):
        assert( routes.rest_request_is_valid({}) == False)

    def test_rest_request_is_valid_options_only(self):
        assert( routes.rest_request_is_valid({"options": None}) == False)

    def test_rest_request_is_valid_options_category(self):
        assert( routes.rest_request_is_valid({"options": None, "category": "/"}) == False)

    def test_rest_request_is_valid_options_category_action(self):
        assert( routes.rest_request_is_valid({"options": None, "category": "/", "action": "help"}) == True)

    def test_rest_request_is_valid_optionslist_category_action(self):
        assert( routes.rest_request_is_valid({"options": {"id": "1"}, "category": "/", "action": "help"}) == True)

    def test_rest_request_is_valid_options_wrongtype(self):
        assert( routes.rest_request_is_valid({"options": [1,2,3], "category": "/", "action": "help"}) == False)

    def test_rest_request_is_valid_category_wrongtype(self):
        assert( routes.rest_request_is_valid({"options": None, "category": [], "action": "help"}) == False)

    def test_rest_request_is_valid_action_wrongtype(self):
        assert( routes.rest_request_is_valid({"options": None, "category": "/", "action": []}) == False)

    def test_rest_request_is_valid_options_invalidinput_value(self):
        assert( routes.rest_request_is_valid({"options": {"id": "<script echo/>"}, "category": "/", "action": "help"}) == False)

    def test_rest_request_is_valid_options_invalidinput_key(self):
        assert( routes.rest_request_is_valid({"options": {"id<script echo/>": "1"}, "category": "/", "action": "help"}) == False)

    def test_rest_request_is_valid_category_invalidinput(self):
        assert( routes.rest_request_is_valid({"options": None, "category": "/<script something>", "action": "help"}) == False)

    def test_rest_request_is_valid_action_invalidinput(self):
        assert( routes.rest_request_is_valid({"options": None, "category": "/", "action": "<script help>"}) == False)

    def test_create_token(self):
        assert ( routes.parse_token(routes.create_token("testuser1"))["sub"] == "testuser1" )

    def test_authenticate_checkstatus(self):
        assert( routes.authenticate().status_code == 401)

    def test_log_action_password_filtering(self):
        api.log_action("jdoe1", {"category": "/users",
                                    "action": "add",
                                    "options": {"username": "test", "password": "secret"}
                                    })
        assert( api.db.logs.find_one({"category": "/users"})["options"]["password"] == "..." )

    def test_log_action_password_nofiltering(self):
        api.log_action("jdoe1", {"category": "/users_nofiltering",
                                    "action": "add",
                                    "options": {"username": "test", "notpassword": "notsecret"}
                                    })
        assert( api.db.logs.find_one({"category": "/users_nofiltering"})["options"]["notpassword"] == "notsecret" )