""" Command Line Interface Module """
import optparse
import sys
import os
import requests
import json
import getpass


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

    def welcome(self):
        """ Welcome Message """
        print("======================")
        print("Welcome To outbit")
        print("Connecting to Server %s" % self.url)
        if self.ping() == "pong":
            print("Connected to Server %s" % self.url)
        else:
            print("Failed connecting to server %s" % self.url)
            print("======================")
            sys.exit(1)
        print("======================")

    def prompt(self):
        """ Command Prompt """
        sys.stdout.write("outbit> ")

    def login_prompt(self):
        if self.user is None:
            self.user = raw_input("Username: ")
        if self.password is None:
            self.password = getpass.getpass()

    def exit(self):
        sys.exit(0)

    def run_action(self, category, action, options):
        jsonobj = {"category": category, "action": action, "options": options}
        r = requests.post(self.url, headers={'Content-Type': 'application/json'},
            auth=(self.user, self.password), data=json.dumps(jsonobj))

        if r.status_code == requests.codes.ok:
            return json.loads(r.text)
        else:
            return None

    def ping(self):
        data = self.run_action("/", "ping", "")
        if data is not None:
            return data["response"]
        else:
            return None

    def add_user(self, username, password):
        data = self.run_action("/users", "add", "%s,%s" % (username, password))
        print("Added user %s: %s" % (username, data["response"]))

    def help(self):
        print("  Command Options:")
        # Todo Print User Added Commands
        print("  exit\n  quit\n  ping\n  help")

    def startshell(self):
        while True:
            line = sys.stdin.readline().strip()
            if line == "quit" or line == "exit":
                print("  Goodbye!")
                self.exit()
            if line == "ping":
                sys.stdout.write("  Ping ..... ")
                print("%s" % self.ping())
            else:
                action = line.split(" ")
                # users add username password
                if action[0] == "users" and action[1] == "add":
                    username = action[2]
                    password = action[3]
                    self.add_user(username, password)
                else:
                    self.help()
            self.prompt()

    def run(self):
        """ EntryPoint Of Application """
        self.login_prompt()
        self.welcome()
        self.prompt()
        self.startshell()
