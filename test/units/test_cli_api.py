import nose
from outbit.cli import api
import sys
import unittest


class TestCli(unittest.TestCase):
    def test_encrypt_str(self):
        # enable encryption pw
        orig = api.encryption_password
        api.encryption_password = "aaaaaaaaaaaaaaaa"
        # encrypt
        enc_str = api.encrypt_str("testabcdtestabcdtestabcd")
        # put it back to whatever it was
        api.encryption_password = orig
        assert(len(enc_str) == 33)

    def test_encrypt_decrypt_str(self):
        # enable encryption pw
        orig = api.encryption_password
        api.encryption_password = "aaaaaaaaaaaaaaaa"
        enc_str = api.encrypt_str("testabcdtestabcdtestabcd")
        dec_str = api.decrypt_str(enc_str)
        # put it back to whatever it was
        api.encryption_password = orig
        assert(len(enc_str) == 33 and dec_str == "testabcdtestabcdtestabcd")

    def test_encrypt_decrypt_dict(self):
        # enable encryption pw
        orig = api.encryption_password
        api.encryption_password = "aaaaaaaaaaaaaaaa"
        test_dict = {"secret": "test", "notsecret": "test"}
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
