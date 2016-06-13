""" Command Line Interface Module """
import optparse
import sys
import os
import requests
import json
import getpass
import curses
from outbit.parser import yacc


class Cli(object):
    """ outbit CLI """

    def __init__(self):
        """ Setup Arguments and Options for CLI """
        # Parse CLI Arguments
        parser = optparse.OptionParser()
        parser.add_option("-u", "--user", dest="user",
                          help="outbit username",
                          metavar="USER",
                          default="superadmin")
        parser.add_option("-s", "--server", dest="server",
                          help="IP address or hostname of outbit-api server",
                          metavar="SERVER",
                          default="127.0.0.1")
        parser.add_option("-p", "--port", dest="port",
                          help="tcp port of outbit-api server",
                          metavar="PORT",
                          default="8088")
        parser.add_option("-t", "--secure", dest="is_secure",
                          help="Use SSL",
                          metavar="SECURE",
                          action="store_true")
        (options, args) = parser.parse_args()
        self.user = options.user
        self.server = options.server
        self.port = int(options.port)
        self.is_secure = options.is_secure
        self.url = "%s://%s:%d" % ("https" if self.is_secure else "http", self.server, self.port)
        self.password = None
        self.screen = None
        self.history = []

    def welcome(self):
        """ Welcome Message """
        self.screen.addstr("======================\n")
        self.screen.addstr("Welcome To outbit\n")
        if "pong" in self.action_ping():
            self.screen.addstr("Connected to Server %s\n" % self.url)
        else:
            print("Failed connecting to server %s\n" % self.url)
            sys.exit(1)
        self.screen.addstr("======================\n")

    def login_prompt(self):
        auth_success = False
        default_username = "superadmin"
        default_pw = "superadmin"

        if self.user is None:
            self.user = raw_input("Username: ")

        for trycount in [1, 2, 3]:
            if self.password is None:
                self.password = getpass.getpass()
            if "pong" in self.action_ping():
                auth_success = True
                if self.user == default_username and self.password == default_pw:
                    for change_trycount in [1, 2, 3]:
                        print("Changing Password From Default")
                        new_password = getpass.getpass("Enter New Password: ")
                        new_password_repeat = getpass.getpass("Enter New Password Again: ")
                        if new_password == new_password_repeat:
                            if self.action_changepw(self.user, new_password) is not "":
                                self.password = new_password
                                break
                break
            else:
                self.password = None

        if auth_success == False:
            print("Login Failed\n")
            sys.exit(1)


    def exit(self):
        sys.exit(0)

    def action_changepw(self, username, password):
        data = self.run_action(self.get_action_from_command("users edit username='%s' password='%s'"
            % (username, password)))
        if data is not None:
            return data["response"]
        else:
            return ""

    def action_ping(self):
        data = self.run_action(self.get_action_from_command("ping"))
        if data is not None:
            return data["response"]
        else:
            return ""

    def is_action_quit(self, action):
        return len(action) == 1 and ( action[0] == "quit" or action[0] == "exit" )

    def action_quit(self):
        self.screen.addstr("  Goodbye!\n")
        self.exit()

    def run_action(self, actionjson):
        r = requests.post(self.url, headers={'Content-Type': 'application/json'},
            auth=(self.user, self.password), data=json.dumps(actionjson))

        if r.status_code == requests.codes.ok:
            return json.loads(r.text)
        else:
            return None

    def get_action_from_command(self, line):
        if line is not None and len(line) > 0:
            # Reset Parser Variables
            yacc.parser_category = None
            yacc.parser_action = None
            yacc.parser_options = None
            # Parse line input
            yacc.parser.parse(line)
            # Return Action Object
            return {'category': yacc.parser_category, "action": yacc.parser_action, "options": yacc.parser_options}
        else:
            return {'category': None, "action": None, "options": None}

    def startshell(self, arg):
        self.screen = curses.initscr()
        self.welcome()
        self.screen.addstr("outbit> ")
        self.screen.keypad(1)
        self.screen.scrollok(1)

        # ctrl-u
        history_index = 0

        # ctrl-r
        search_mode = False
        last_match = None

        line = ""
        while True:
            s = self.screen.getch()

            # Ascii
            if s >= 32 and s <= 126:
                line += chr(s)
                if search_mode:
                    match = None
                    for item in reversed(self.history):
                        if line in item:
                            match = item
                            break
                    if match is None:
                        self.screen.addstr(y, 0, "(reverse-i-search)`':")
                        self.screen.addstr(y, len("(reverse-i-search)`':"), line)
                        self.screen.clrtoeol()
                    else:
                        (y, x) = self.screen.getyx()
                        self.screen.addstr(y, 0, "(reverse-i-search)`':")
                        self.screen.addstr(y, len("(reverse-i-search)`':"), match)
                        self.screen.clrtoeol()
                        last_match = match
                else:
                    self.screen.addstr(chr(s))
                history_index = 0
            # Finished With Line Input
            elif s == ord("\n"):
                self.screen.addstr("\n")
                if search_mode:
                    if match is not None:
                        self.shell_parse_line(match)
                else:
                    self.shell_parse_line(line)
                self.screen.addstr("\noutbit> ")
                line = ""
                history_index = 0
                search_mode = False
            # Backspace
            elif s == curses.KEY_BACKSPACE or s == 127 or s == curses.erasechar():
                line = line[:-1]
                (y, x) = self.screen.getyx()
                self.screen.addstr(y, 0, "outbit> ")
                self.screen.addstr(y, len("outbit> "), line)
                self.screen.clrtoeol()
                history_index = 0
            # Ctrl-u, clear line
            elif s == 21:
                (y, x) = self.screen.getyx()
                self.screen.addstr(y, 0, "outbit> ")
                self.screen.clrtoeol()
                line = ""
                history_index = 0
            # Ctrl-r, search
            elif s == 18:
                search_mode = True
                (y, x) = self.screen.getyx()
                self.screen.addstr(y, 0, "(reverse-i-search)`':")
                self.screen.clrtoeol()
                line = ""
                history_index = 0
            elif s == curses.KEY_UP:
                if len(self.history) < 1:
                    # prevent divide by zero when history is 0
                    continue
                history_index += 1
                (y, x) = self.screen.getyx()
                self.screen.addstr(y, 0, "outbit> ")
                self.screen.addstr(y, len("outbit> "), self.history[-(history_index%len(self.history))])
                self.screen.clrtoeol()
                line = self.history[-(history_index%len(self.history))]
            elif s == curses.KEY_DOWN:
                if len(self.history) < 1:
                    # prevent divide by zero when history is 0
                    continue
                history_index -= 1
                (y, x) = self.screen.getyx()
                self.screen.addstr(y, 0, "outbit> ")
                self.screen.addstr(y, len("outbit> "), self.history[-(history_index%len(self.history))])
                self.screen.clrtoeol()
                line = self.history[-(history_index%len(self.history))]
            else:
                #self.screen.addstr("Out of range: %d" % s)
                history_index = 0

        curses.endwin()

    def shell_parse_line(self, line):
        line = line.strip()
        action = line.split()
        if self.is_action_quit(action):
            # outbit> quit
            # outbit> exit
            self.action_quit()
        else:
            # Server Side Handles Command Response
            # outbit> [category ..] action [option1=something ..]
            if line is not None and len(line) > 0:
                self.history.append(line)

            actionjson = self.get_action_from_command(line)
            data = self.run_action(actionjson)
            if data is not None:
                self.screen.addstr(data["response"])
                return data["response"]
            else:
                response = "outbit - Failed To Get Response From Server\n"
                self.screen.addstr(response)
                return(response)

    def run(self):
        """ EntryPoint Of Application """
        self.login_prompt()
        curses.wrapper(self.startshell)
