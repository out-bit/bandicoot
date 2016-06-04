import nose
from outbit.cli.api import Cli
import unittest
import sys
import os

class TestCli(unittest.TestCase):
    def test_project(self):
        # Test No Path Given (Hello Test)
        sys.argv[1] = ""
        sys.argv[2] = ""
        cli = Cli()
        assert(cli is not None)
