import nose
from outbit.cli import api
import sys
import unittest


class TestCli(unittest.TestCase):
    def test_project(self):
        # Test No Path Given (Hello Test)
        sys.argv[1] = ""
        sys.argv[2] = ""
        cli = api.Cli()
        assert(cli is not None)
