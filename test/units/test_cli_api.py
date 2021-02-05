import nose
from bandicoot.cli import api
import sys
import unittest
import mongomock
import json


class TestCli(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        self.mock_db_setup()
        self.mock_db_basic_database()
        unittest.TestCase.__init__(self, *args, **kwargs)

    def mock_db_setup(self):
        api.dbclient = mongomock.MongoClient()
        api.db = api.dbclient.conn["bandicoot"]

    def mock_db_basic_database(self):
        api.db.users.insert_one({"username": "jdoe1", "password_md5": "md5test"})
        api.db.users.insert_one({"username": "jdoe2", "password_md5": "md5test"})
        api.db.secrets.insert_one({"name": "test_secret1", "secret": "__bandicoot_encrypted__:"+"test"})
        api.db.roles.insert_one({"name": "test_role1", "users": "jdoe1", "actions": "/", "secrets": "test_secret1"})

    def test_counters_db_init(self):
        api.counters_db_init("testseq")
        assert(api.db.counters.find_one({"_id": "testseq"}) != None)

    def test_counters_db_getNextSequence(self):
        api.counters_db_init("testseq")
        assert(api.counters_db_getNextSequence("testseq") == 1)

    def test_render_secrets_nonedict(self):
        assert(api.render_secrets("jdoe1", None) == None)

    def test_render_secrets_noperm(self):
        testobj = {"a": "hello {{ test_secret1 }}", "b": "no render"}
        res = api.render_secrets("jdoe2", testobj)
        print("%s, %s" % (res, testobj))
        assert(testobj["a"] == "hello ")

#    def test_render_secrets(self):
#        testobj = {"a": "hello {{ test_secret1 }}", "b": "no render"}
#        api.render_secrets("jdoe1", testobj)
#        assert(testobj["a"] == "hello test")

    def test_parse_action_noperm(self):
        response = api.parse_action("jdoe2", "/users", "list", {})
        assert(response == json.dumps({"response": "  you do not have permission to run this action"}))

    def test_encrypt_str(self):
        # encrypt
        enc_str = api.encrypt_str("testabcdtestabcdtestabcd", encrypt_password="aaaaaaaaaaaaaaaa")
        print(len(enc_str))
        assert(len(enc_str) == 61)

    def test_encrypt_decrypt_str(self):
        enc_str = api.encrypt_str("testabcdtestabcdtestabcd", encrypt_password="aaaaaaaaaaaaaaaa")
        dec_str = api.decrypt_str(enc_str, encrypt_password="aaaaaaaaaaaaaaaa")
        print("%s, %s" % (len(enc_str), dec_str))
        assert(len(enc_str) == 61 and dec_str == "testabcdtestabcdtestabcd")

    def test_encrypt_decrypt_dict_exception(self):
        # enable encryption pw
        test_dict = {"name": "testsecret", "secret": "test", "notsecret": "test"}
        assert( api.decrypt_dict(test_dict) == False )

    def test_encrypt_decrypt_dict(self):
        # enable encryption pw
        orig = api.encryption_password
        api.encryption_password = "aaaaaaaaaaaaaaaa"
        test_dict = {"name": "testsecret", "secret": "test", "notsecret": "test"}
        api.encrypt_dict(test_dict)
        api.decrypt_dict(test_dict)
        # put it back to whatever it was
        api.encryption_password = orig
        assert(test_dict["secret"] == "test" and test_dict["notsecret"] == "test")

    def test_project(self):
        # Test No Path Given (Hello Test)
        sys.argv[1] = ""
        sys.argv[2] = ""
        cli = api.Cli()
        assert(cli is not None)
