import nose
import unittest
import sys
import json
from StringIO import StringIO
import requests_mock
from mock import patch
from outbit.cli import cli


class TestCli(unittest.TestCase):

    @requests_mock.mock()
    @patch('getpass.getpass', return_value='password') # Mock password typed in stdin
    def test_run_noninteractive_ping(self, m, mock_getpass):
        saved_stdout = sys.stdout
        output = None
        try:
            out = StringIO()
            sys.stdout = out

            m.post("http://127.0.0.1:8088/", text=json.dumps({"response": "  pong"}))
            cliobj = cli.Cli()
            cliobj.interactive_mode = False
            cliobj.noninteractive_commands = ["ping"]
            cliobj.run()

            output = out.getvalue().strip() # because i dont care about spaces
            assert( output == "pong" )
        finally:
            sys.stdout = saved_stdout


