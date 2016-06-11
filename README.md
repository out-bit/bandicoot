outbit
=====================

Description
===========

outbit - The command line and control center of a Data Center or Cloud.

[![Build Status](https://secure.travis-ci.org/starboarder2001/outbit.png?branch=develop "outbit latest build")](http://travis-ci.org/starboarder2001/outbit)
[![PIP Version](https://img.shields.io/pypi/v/outbit.svg "outbit PyPI version")](https://pypi.python.org/pypi/outbit)
[![PIP Downloads](https://img.shields.io/pypi/dm/outbit.svg "outbit PyPI downloads")](https://pypi.python.org/pypi/outbit)
[![Coverage Status](https://coveralls.io/repos/github/starboarder2001/outbit/badge.svg?branch=develop)](https://coveralls.io/github/starboarder2001/outbit?branch=develop)
[![Gitter IM](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/starboarder2001/outbit)


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
outbit> exit
```
