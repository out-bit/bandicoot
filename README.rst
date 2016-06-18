.. image:: https://secure.travis-ci.org/starboarder2001/outbit.png?branch=develop
        :target: http://travis-ci.org/starboarder2001/outbit
        :alt: Travis CI

.. image:: https://img.shields.io/pypi/dm/outbit.svg
    :target: https://pypi.python.org/pypi/outbit
    :alt: Number of PyPI downloads
    
.. image:: https://img.shields.io/pypi/v/outbit.svg
    :target: https://pypi.python.org/pypi/outbit
    :alt: PyPI version

.. image:: https://badges.gitter.im/Join%20Chat.svg
   :alt: Join the chat at https://gitter.im/starboarder2001/outbit
   :target: https://gitter.im/starboarder2001/outbit?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge

.. image:: https://coveralls.io/repos/starboarder2001/outbit/badge.svg?branch=develop
    :target: https://coveralls.io/r/starboarder2001/outbit?branch=develop

.. image:: https://readthedocs.org/projects/outbit/badge/?version=develop
    :target: http://outbit.readthedocs.org/en/latest/?badge=develop
    :alt: Documentation Status

outbit
============

outbit provides a simple UI (CLI and eventually a web based GUI) for orchestrating changes or applying configurations in a datacenter or cloud environment.  outbit provides a layer on top of Ansible (other DevOps tools can be added in the future) that allows you to easily wrap up automated tasks and provide a simple way to execute them.  The role based access control allows you to implement seperations of duties and limit specific actions to be executed by specific roles.  The logging feature allows you to track the history of changes in the environment.  outbit is an alternative to tools such as Ansible Tower, Foreman, and rundeck.

Installation
============

.. sourcecode:: bash

    pip install outbit

or

.. sourcecode:: bash

    easy_install outbit

Usage
============

Start the API server on your localhost or on a dedicated server

.. sourcecode:: bash

    $ outbit-api

Login to the outbit shell

.. sourcecode:: bash

    $ outbit -u superadmin
      Password: superadmin

Add a "hello world" action that prints hello world

.. sourcecode:: bash

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

License
============
outbit is released under the MIT License

Author
============
David Whiteside (david@davidwhiteside.com)
