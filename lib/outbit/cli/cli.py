""" Command Line Interface Module """
import optparse
import sys
import os
import requests
import json
import getpass
import curses
import ply.yacc as yacc
import ply.lex as lex


# LEX tokens
tokens = ("ACTION", "OPTIONVAL", "OPTIONVALS", "OPTIONVALD", "SPACE", "EQUAL")

t_ACTION        =r'[a-zA-Z0-9_\-]+'
t_OPTIONVAL     =r'/[a-zA-Z0-9_/\-]+'
t_OPTIONVALS    =r"'[\"a-zA-Z0-9_/\s\-]+'"
t_OPTIONVALD    =r'"[\'a-zA-Z0-9_/\s\-]+"'
t_SPACE         =r'\s+'
t_EQUAL         =r'='

# Ignored characters
t_ignore = "\n"

def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

# Build the lexer
lexer = lex.lex()

parser_category = "/"
parser_action = ""
parser_options = {}

# YACC parser
precedence = (
    ('left', 'SPACE'),
    )

def p_action_run(t):
    '''action_run : actions SPACE options
              | actions'''
    global parser_category
    global parser_action
    global parser_options
    if len(t) == 4:
        parser_category = "/%s" % "/".join(t[1][:-1])
        parser_action = t[1][-1]
        parser_options = t[3]
    elif len(t) == 2:
        parser_category = "/%s" % "/".join(t[1][:-1])
        parser_action = t[1][-1]
    else:
        print("error in action_run %d\n" % len(t))

def p_actions(t):
    '''actions : actions SPACE ACTION
              | ACTION'''
    if t[0] is None:
        t[0] = []
    if len(t) == 4:
        if isinstance(t[1], list):
            t[0] += t[1]
        else:
            t[0].append(t[1])
        t[0].append(t[3])
    elif len(t) == 2:
        t[0].append(t[1])
    else:
        print("error in action %d\n" % len(t))

def p_options(t):
    '''options : options SPACE option
               | option'''
    if t[0] is None:
        t[0] = {}
    if len(t) == 4:
        t[0].update(t[1])
        t[0].update(t[3])
    elif len(t) == 2:
        t[0].update(t[1])
    else:
        print("error in options %d\n" % len(t))

def p_option(t):
    '''option : ACTION EQUAL ACTION
              | ACTION EQUAL OPTIONVAL
              | ACTION EQUAL OPTIONVALS
              | ACTION EQUAL OPTIONVALD'''
    if t[0] is None:
        t[0] = {}
    if t[3][0] is "'":
        t[0][t[1]] = t[3].strip("'")
    elif t[3][0] is '"':
        t[0][t[1]] = t[3].strip('"')
    else:
        t[0][t[1]] = t[3]

def p_error(t):
    print("Syntax error at '%s'" % t.value)

parser = yacc.yacc()


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
        self.screen.addstr("Connecting to Server %s\n" % self.url)
        if "pong" in self.action_ping():
            self.screen.addstr("Connected to Server %s\n" % self.url)
        else:
            self.screen.addstr("Failed connecting to server %s\n" % self.url)
            self.screen.addstr("======================\n")
            sys.exit(1)
        self.screen.addstr("======================\n")

    def login_prompt(self):
        if self.user is None:
            self.user = raw_input("Username: ")
        if self.password is None:
            self.password = getpass.getpass()

    def exit(self):
        sys.exit(0)

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
        parser.parse(line)
        return {'category': parser_category, "action": parser_action, "options": parser_options}

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
                        self.history.append(match)
                else:
                    self.shell_parse_line(line)
                    self.history.append(line)
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
                self.screen.addstr("Out of range: %d" % s)
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
