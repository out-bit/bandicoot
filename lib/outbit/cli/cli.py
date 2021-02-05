""" Command Line Interface Module """
import optparse
import sys
import os
import requests
import json
import yaml
import getpass
import curses
import time
import signal
from bandicoot.parser import yacc

session = requests.Session()
sig_bg_pressed = 0
sig_kill_pressed = 0

# UNICODE
import locale
locale.setlocale(locale.LC_ALL, '')

# catch ctrl-z
def sig_background(signum, frame):
    global sig_bg_pressed
    sig_bg_pressed = 1


# catch ctrl-c
def sig_kill(signum, frame):
    global sig_kill_pressed
    sig_kill_pressed = 1


# signal for ctrl-z
signal.signal(signal.SIGTSTP, sig_background)
# signal for ctrl-c
signal.signal(signal.SIGINT, sig_kill)


class Cli(object):
    """ bandicoot CLI """

    def __init__(self):
        """ Setup Arguments and Options for CLI """
        # Parse CLI Arguments
        parser = optparse.OptionParser()
        parser.add_option("-u", "--user", dest="user",
                          help="bandicoot username",
                          metavar="USER",
                          default=None)
        parser.add_option("-s", "--server", dest="server",
                          help="IP address or hostname of bandicoot-api server",
                          metavar="SERVER",
                          default=None)
        parser.add_option("-p", "--port", dest="port",
                          help="tcp port of bandicoot-api server",
                          metavar="PORT",
                          default=None)
        parser.add_option("-t", "--insecure", dest="is_secure",
                          help="Do Not Use SSL",
                          metavar="SECURE",
                          action="store_false",
                          default=True)
        parser.add_option("-k", "--no-check-certificates", dest="is_ssl_verify",
                          help="Ignore Unverified Certificate",
                          metavar="VERIFY",
                          action="store_false",
                          default=True)
        # Assign values from cli
        (options, args) = parser.parse_args()
        self.user = options.user
        self.server = options.server
        self.port = options.port
        self.is_secure = options.is_secure
        self.is_ssl_verify = options.is_ssl_verify
        self.interactive_mode = True
        self.noninteractive_commands = []
        self.password = None
        self.app_running = True

        # Do Not Display SSL Verify Warning to stderr
        requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

        # Non-Interactive Command Parsing
        if len(args) > 0:
            self.interactive_mode = False
            for command in args:
                self.noninteractive_commands.append(command)

        # Assign values from conf
        bandicoot_config_locations = [os.path.expanduser("~")+"/.bandicoot.conf", "/etc/bandicoot.conf"]
        bandicoot_conf_obj = {}
        for bandicoot_conf in bandicoot_config_locations:
            if os.path.isfile(bandicoot_conf):
                with open(bandicoot_conf, 'r') as stream:
                    try:
                        bandicoot_conf_obj = yaml.load(stream)
                    except yaml.YAMLError as excep:
                        print("%s\n" % excep)
        if self.user is None and "user" in bandicoot_conf_obj:
            self.user = str(bandicoot_conf_obj["user"])
        if self.password is None and "password" in bandicoot_conf_obj:
            self.password = str(bandicoot_conf_obj["password"])
        if self.server is None and "server" in bandicoot_conf_obj:
            self.server = str(bandicoot_conf_obj["server"])
        if self.port is None and "port" in bandicoot_conf_obj:
            self.port = int(bandicoot_conf_obj["port"])
        if self.is_secure == True and "secure" in bandicoot_conf_obj:
            self.is_secure = bool(bandicoot_conf_obj["secure"])
        if self.is_ssl_verify == True and "ssl_verify" in bandicoot_conf_obj:
            self.is_ssl_verify = bool(bandicoot_conf_obj["ssl_verify"])

        # Assign Default values if they were not specified at the cli or in the conf
        if self.user is None:
            self.user = "superadmin"
        if self.server is None:
            self.server = "127.0.0.1"
        if self.port is None:
            self.port = 8088

        self.url = "%s://%s:%d" % ("https" if self.is_secure else "http", str(self.server), int(self.port))
        self.screen = None
        self.history = []

    def welcome(self):
        """ Welcome Message """
        self.screen.addstr("======================\n")
        self.screen.addstr("Welcome To bandicoot\n")
        if "pong" in self.action_ping():
            self.screen.addstr("Connected to Server %s\n" % self.url)
        else:
            print("Failed connecting to server %s\n" % self.url)
            self.exit(1)
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
            self.exit(1)


    def exit(self, val):
        sys.exit(val)
        self.app_running = False # For unit testing

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
        self.exit(0)

    def run_action(self, actionjson):
        r = session.post(self.url, verify=self.is_ssl_verify, headers={'Content-Type': 'application/json'},
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
            yacc.parser_error = None
            # Parse line input
            yacc.parser.parse(line)
            # Return Action Object
            return {'category': yacc.parser_category, "action": yacc.parser_action, "options": yacc.parser_options}
        else:
            return {'category': None, "action": None, "options": None}

    def startshell(self, arg):
        self.screen = curses.initscr()
        self.welcome()
        curses.curs_set(1)
        self.screen.addstr("bandicoot> ")
        self.screen.keypad(1)
        self.screen.scrollok(1)

        # left and right key
        cursor_offset = 0

        # ctrl-u
        history_index = 0

        # ctrl-r
        search_mode = False
        last_match = None

        line = ""
        while self.app_running:
            s = self.screen.getch()

            # Ascii
            if s >= 32 and s <= 126:
                if cursor_offset >= 0:
                    # cursor at end of line
                    line += chr(s)
                    self.screen.addstr(chr(s))
                elif cursor_offset <= len(line)*-1:
                    # cursor at beginning of line
                    line = chr(s) + line
                    self.screen.insstr(chr(s))
                    (y, x) = self.screen.getyx()
                    self.screen.move(y, x+1)
                else:
                    # cursor in the middle of the line
                    line = line[:len(line)+cursor_offset] + chr(s) + line[len(line)+cursor_offset:]
                    self.screen.insstr(chr(s))
                    (y, x) = self.screen.getyx()
                    self.screen.move(y, x+1)
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
                history_index = 0
            # Finished With Line Input
            elif s == ord("\n"):
                (y, x) = self.screen.getyx()
                self.screen.move(y, len("bandicoot> ")+len(line))
                self.screen.addstr("\n")
                if search_mode:
                    if match is not None:
                        result = self.shell_parse_line(match)
                        self.screen.addstr(result)
                else:
                    result = self.shell_parse_line(line)
                    if result is not None:
                        self.screen.addstr(result.encode("UTF-8"))
                self.screen.addstr("\nbandicoot> ")
                line = ""
                history_index = 0
                cursor_offset = 0
                search_mode = False
            # Backspace
            elif s == curses.KEY_BACKSPACE or s == 127 or s == curses.erasechar():
                (y, x) = self.screen.getyx()
                if len(line) > 0 and x > len("bandicoot> "):
                    line = line[:len(line)+cursor_offset-1] + line[len(line)+cursor_offset:]
                    self.screen.delch(y, x-1)
                history_index = 0
            # Ctrl-u, clear line
            elif s == 21:
                (y, x) = self.screen.getyx()
                self.screen.addstr(y, 0, "bandicoot> ")
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
                cursor_offset = 0
                (y, x) = self.screen.getyx()
                self.screen.addstr(y, 0, "bandicoot> ")
                self.screen.addstr(y, len("bandicoot> "), self.history[-(history_index%len(self.history))])
                self.screen.clrtoeol()
                line = self.history[-(history_index%len(self.history))]
            elif s == curses.KEY_DOWN:
                if len(self.history) < 1:
                    # prevent divide by zero when history is 0
                    continue
                history_index -= 1
                cursor_offset = 0
                (y, x) = self.screen.getyx()
                self.screen.addstr(y, 0, "bandicoot> ")
                self.screen.addstr(y, len("bandicoot> "), self.history[-(history_index%len(self.history))])
                self.screen.clrtoeol()
                line = self.history[-(history_index%len(self.history))]
            elif s == curses.KEY_LEFT:
                if cursor_offset > len(line)*-1:
                    cursor_offset -= 1
                    (y, x) = self.screen.getyx()
                    self.screen.move(y, x-1)
            elif s == curses.KEY_RIGHT:
                if cursor_offset < 0:
                    cursor_offset += 1
                    (y, x) = self.screen.getyx()
                    self.screen.move(y, x+1)
            else:
                #self.screen.ddstr("Out of range: %d" % s)
                history_index = 0
                cursor_offset = 0

        curses.endwin()

    def blocking_get_response_queued_job(self, queue_id):
        global sig_bg_pressed
        global sig_kill_pressed
        sig_bg_pressed = 0 # Reset ctrl-z state
        sig_kill_pressed = 0 # reset ctrl-c state

        data = {"response": "  "}
        last_response = ""
        self.screen.addstr("\nJob is running with id=%s. Press ctrl-z to background job.\n" % str(queue_id))
        self.screen.refresh()

        while sig_bg_pressed == 0:
            if sig_kill_pressed == 1:
                # Kill job
                data = self.run_action(self.get_action_from_command("jobs kill id=%s" % str(queue_id)))
                self.screen.addstr(data["response"])
                self.screen.refresh()
                break
            else:
                data = self.run_action(self.get_action_from_command("jobs status id=%s" % str(queue_id)))
                if data is None or "finished" not in data or data["finished"] == True:
                    # Its finished, print the last update
                    updatestr = data["response"].replace(last_response, "")
                    self.screen.addstr(updatestr)
                    self.screen.refresh()
                    return "" # prints no update since everything was already printed to the screen
                if "response" in data and "exit_code" in data and data["exit_code"] != 0:
                    # Error happend
                    return data["response"] # prints error string
                updatestr = data["response"].replace(last_response, "")
                self.screen.addstr(updatestr)
                self.screen.refresh()
                last_response = data["response"]
                time.sleep(5)
        return "" # no update

    def shell_parse_line(self, line):
        line = line.strip()

        # Return nothing for an empty line
        if len(line) <= 0:
            return("")

        action = line.split()
        if self.is_action_quit(action):
            # bandicoot> quit
            # bandicoot> exit
            self.action_quit()
        else:
            # Server Side Handles Command Response
            # bandicoot> [category ..] action [option1=something ..]
            if line is not None and len(line) > 0:
                self.history.append(line)

            actionjson = self.get_action_from_command(line)
            if yacc.parser_error is None:
                data = self.run_action(actionjson)
            else:
                data = {"response": yacc.parser_error}
            if data is not None:
                if "response" in data:
                    return data["response"]
                elif "queue_id" in data:
                    return self.blocking_get_response_queued_job(data["queue_id"])
                else:
                    return("bandicoot - Invalid Response From server\n")
            else:
                return("bandicoot - Failed To Get Response From Server\n")

    def run(self):
        """ EntryPoint Of Application """
        self.login_prompt()
        if self.interactive_mode:
            curses.wrapper(self.startshell)
        else:
            for command in self.noninteractive_commands:
                print(self.shell_parse_line(command))
