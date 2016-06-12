import nose
from outbit.cli import cli
import unittest
import sys
import os

class TestCli(unittest.TestCase):
    def test_project(self):
        # Test No Path Given (Hello Test)
        sys.argv[1] = ""
        sys.argv[2] = ""
        cliobj = cli.Cli()
        assert(cliobj is not None)
