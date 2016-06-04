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
        if "pong" in self.action_ping():
            print("Connected to Server %s" % self.url)
        else:
            print("Failed connecting to server %s" % self.url)
            print("======================")
            sys.exit(1)
        print("======================")

    def prompt(self):
        """ Command Prompt """
        sys.stdout.write("%s@outbit> " % self.user)

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
        print("  Goodbye!")
        self.exit()

    def run_action(self, actionjson):
        r = requests.post(self.url, headers={'Content-Type': 'application/json'},
            auth=(self.user, self.password), data=json.dumps(actionjson))

        if r.status_code == requests.codes.ok:
            return json.loads(r.text)
        else:
            return None

    def get_action_from_command(self, line):
        action_list = line.strip().split()
        actionjson = {'category': "/", "action": "", "options": ""}
        if len(action_list) == 1:
            actionjson = {'category': "/", "action": action_list[0], "options": ""}
        elif len(action_list) >= 2:
            category = "/"
            action = ""
            options = ""
            count = 0 # Count number of options
            action_list_reverse = list(action_list)
            action_list_reverse.reverse()
            for node in action_list_reverse:
                if category is "/" and action is "" and "=" in node:
                    options += "%s," % node
                    count += 1
                elif category is "/" and action is "" and "=" not in node:
                    action = node
                    count += 1
                else:
                    category_range = len(action_list) - count
                    category = "/%s" % "/".join(action_list[0:category_range])
            actionjson = {'category': category, "action": action, "options": options}

        return actionjson

    def startshell(self):
        while True:
            line = sys.stdin.readline().strip()
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
                    print(data["response"])
                else:
                    print("outbit - Failed To Get Response From Server")
            self.prompt()

    def run(self):
        """ EntryPoint Of Application """
        self.login_prompt()
        self.welcome()
        self.prompt()
        self.startshell()
