""" Command Line Interface Module """
import optparse
import sys
import os
import requests
import json


class Cli(object):
    """ outbit CLI """

    def __init__(self):
        """ Setup Arguments and Options for CLI """
        # Parse CLI Arguments
        parser = optparse.OptionParser()
        parser.add_option("-u", "--user", dest="user",
                          help="outbit username",
                          metavar="USER")
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

    def welcome(self):
        """ Welcome Message """
        print("======================")
        print("Welcome To outbit")
        print("connected to server %s" % self.url)
        print("======================")

    def prompt(self):
        """ Command Prompt """
        sys.stdout.write("outbit> ")

    def exit(self):
        sys.exit(0)

    def run_action(self, category, action, options):
        jsonobj = '{"category": "%s", "action": "%s", "options": "%s"}'
        response = requests.get(self.url, data=jsonobj)
        return json.loads(response.text)

    def ping(self):
        sys.stdout.write("Ping ..... ")
        data = self.run_action("/", "ping", "")
        print("Pong: %s" % data["response"])

    def help(self):
        print("  Command Options:")
        # Todo Print User Added Commands
        print("  exit\n  quit\n  ping\n  help")

    def startshell(self):
        while True:
            line = sys.stdin.readline().strip()
            if line == "quit" or line == "exit":
                self.exit()
            if line == "ping":
                self.ping()
            else:
                self.help()
            self.prompt()

    def run(self):
        """ EntryPoint Of Application """
        self.welcome()
        self.prompt()
        self.startshell()
