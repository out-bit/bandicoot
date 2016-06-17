[![Build Status](https://secure.travis-ci.org/starboarder2001/outbit.png?branch=develop "outbit latest build")](http://travis-ci.org/starboarder2001/outbit)
[![PIP Version](https://img.shields.io/pypi/v/outbit.svg "outbit PyPI version")](https://pypi.python.org/pypi/outbit)
[![PIP Downloads](https://img.shields.io/pypi/dm/outbit.svg "outbit PyPI downloads")](https://pypi.python.org/pypi/outbit)
[![Coverage Status](https://coveralls.io/repos/github/starboarder2001/outbit/badge.svg?branch=develop)](https://coveralls.io/github/starboarder2001/outbit?branch=develop)
[![Gitter IM](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/starboarder2001/outbit)

outbit
===========

outbit provides a simple UI (CLI and eventually a web based GUI) for orchestrating changes or applying configurations in a datacenter or cloud environment.  outbit provides a layer on top of Ansible (other DevOps tools can be added in the future) that allows you to easily wrap up automated tasks and provide a simple way to execute them.  The role based access control allows you to implement seperations of duties and limit specific actions to be executed by specific roles.  The logging feature allows you to track the history of changes in the environment.  outbit is an alternative to tools such as Ansible Tower, Foreman, and rundeck.

Installation
===========

```shell
pip install outbit
```

or

```shell
easy_install outbit
```

Usage
===========

Start the API server on your localhost or on a dedicated server
```shell
$ outbit-api
```

Login to the outbit shell
```shell
$ outbit -u superadmin
  Password: superadmin
```

Add a "hello world" action that prints hello world
```shell
======================
Welcome To outbit
Connecting to Server http://127.0.0.1:8088
Connected to Server http://127.0.0.1:8088
======================
outbit> help
  actions list          list actions
  actions del           del actions
  actions add           add actions
  users list            list users
  users del             del users
  users add             add users
  roles list            list roles
  roles del             del roles
  roles add             add roles
  plugins list          list plugins
  ping                  verify connectivity
  logs                  show the history log
  help                  print usage

outbit> actions add category=/testing name=helloworld plugin=command action=helloworld desc="print hello world" command_run="echo 'hello world'"

outbit> help
  actions list          list actions
  actions del           del actions
  actions add           add actions
  users list            list users
  users del             del users
  users add             add users
  roles list            list roles
  roles del             del roles
  roles add             add roles
  plugins list          list plugins
  ping                  verify connectivity
  logs                  show the history log
  help                  print usage
  testing helloworld           print hello world

outbit> testing helloworld
  hello world
  return code: 0

outbit> exit
```

License
===========
outbit is released under the MIT License

Author
===========
David Whiteside (david@davidwhiteside.com)
