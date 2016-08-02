import nose
import unittest
import sys
import json
import curses
from StringIO import StringIO
import requests_mock
from mock import patch
from outbit.cli import cli


class CursesMock(object):
    def __init__(self, inputstr):
        self.screen = ""
        self.inputstr = str(inputstr)
        self.cursor_pos_x = 0
        self.cursor_pos_y = 0
        self.cscreen = curses.initscr()

    def addstr(self, s):
        self.screen += str(s)

    def insstr(self, s):
        pass

    def keypad(self, i):
        pass

    def scrollok(self, i):
        pass

    def getch(self):
        c = "\n"
        if self.cursor_pos_x < len(self.inputstr):
            c = self.inputstr[self.cursor_pos_x]
            self.cursor_pos_x += 1
        return ord(c)

    def delch(self,y, x):
        pass

    def move(self, y, x):
        pass

    def getyx(self):
        return (self.cursor_pos_y, self.cursor_pos_x)

    def clrtoeol(self):
        pass

    def echo(self):
        pass


def curses_wrapper_mock(func):
    func("arg")


def create_curses_wrapper_mock():
    return curses_wrapper_mock
    

class TestCli(unittest.TestCase):

    @requests_mock.mock()
    @patch('getpass.getpass', return_value='password') # Mock password typed in stdin
    def test_run_noninteractive_ping(self, m, mock_getpass):
        saved_stdout = sys.stdout
        output = None
        try:
            out = StringIO()
            sys.stdout = out

            m.post("https://127.0.0.1:8088/", text=json.dumps({"response": "  pong"}))
            cliobj = cli.Cli()
            cliobj.interactive_mode = False
            cliobj.noninteractive_commands = ["ping"]
            cliobj.run()

            output = out.getvalue().strip() # because i dont care about spaces
            assert( output == "pong" )
        finally:
            sys.stdout = saved_stdout

    @requests_mock.mock()
    @patch('sys.exit', return_value=0)
    @patch('curses.initscr', return_value=CursesMock("ping\nexit\n"))
    @patch('getpass.getpass', return_value='password') # Mock password typed in stdin
    def test_run_interactive_ping(self, m, mock_getpass, mock_initscr, mock_exit):
        m.post("https://127.0.0.1:8088/", text=json.dumps({"response": "  pong"}))
        cliobj = cli.Cli()
        cliobj.interactive_mode = True
        cliobj.run()
        curses.endwin()
        print(mock_initscr.return_value.screen)
        assert( "Goodbye!" in mock_initscr.return_value.screen )
