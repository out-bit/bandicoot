import nose
import unittest
from outbit.cli import api
from outbit.restapi import routes
import mongomock
from flask import Response


class TestCli(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        self.mock_db_setup()
        self.mock_db_basic_database()
        unittest.TestCase.__init__(self, *args, **kwargs)

    def mock_db_setup(self):
        api.dbclient = mongomock.MongoClient()
        api.db = api.dbclient.conn["outbit"]

    def mock_db_basic_database(self):
        api.db.users.insert_one({"username": "jdoe1", "password_md5": "5f4dcc3b5aa765d61d8327deb882cf99"})

        api.db.actions.insert_one({"name": "test_action1", "category": "/testing", "action": "pwd", "plugin": "command", "command_run": "echo 'hello world'", "desc": "test pwd"})

        api.db.roles.insert_one({"name": "test_role1", "users": "jdoe2", "actions": "/", "secrets": "test_secret1"})

        api.db.secrets.insert_one({"name": "test_secret1", "secret": "foundme1"})

    def test_check_auth_fail(self):
        assert( routes.check_auth("jdoe1", "wrongpw") == False )

    def test_check_auth(self):
        assert( routes.check_auth("jdoe1", "password") == True )

    def test_authenticate_checkstatus(self):
        assert( routes.authenticate().status_code == 401)

    def test_log_action_password_filtering(self):
        routes.log_action("jdoe1", {"category": "/users",
                                    "action": "add",
                                    "options": {"username": "test", "password": "secret"}
                                    })
        assert( api.db.logs.find_one({"category": "/users"})["options"]["password"] == "..." )

    def test_log_action_password_nofiltering(self):
        routes.log_action("jdoe1", {"category": "/users_nofiltering",
                                    "action": "add",
                                    "options": {"username": "test", "notpassword": "notsecret"}
                                    })
        assert( api.db.logs.find_one({"category": "/users_nofiltering"})["options"]["notpassword"] == "notsecret" )