outbit
============

.. image:: https://secure.travis-ci.org/starboarder2001/outbit.png?branch=master
        :target: http://travis-ci.org/starboarder2001/outbit
        :alt: Travis CI

.. image:: https://img.shields.io/pypi/v/outbit.svg
    :target: https://pypi.python.org/pypi/outbit
    :alt: PyPI version

.. image:: https://badges.gitter.im/Join%20Chat.svg
   :alt: Join the chat at https://gitter.im/starboarder2001/outbit
   :target: https://gitter.im/starboarder2001/outbit?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge

.. image:: https://coveralls.io/repos/starboarder2001/outbit/badge.svg?branch=master
    :target: https://coveralls.io/r/starboarder2001/outbit?branch=master

.. image:: https://readthedocs.org/projects/outbit/badge/?version=stable
    :target: http://outbit.readthedocs.io/en/stable/
    :alt: Documentation Status

outbit provides a simple UI for orchestrating changes or applying configurations in a datacenter and cloud environment.  outbit provides a layer on top of Ansible that allows you to easily wrap up automated tasks and provide a simple way to execute them.  The role based access control allows you to implement seperations of duties and limit specific actions to be executed by specific roles.  The logging feature allows you to track the history of changes in the environment.

Installation
============

Install outbit client only. This is if you already have a dedicated outbit api server.

.. sourcecode:: bash

    $ pip install outbit

Install outbit api server.

.. sourcecode:: bash

  $ pip install outbit
  $ sudo outbit-api-install

Install and Starting the outbit api server using Docker.

.. sourcecode:: bash

  $ docker pull starboarder2001/outbit
  $ docker run -d -p 8088:8088 -p 80:80 -p 443:443 starboarder2001/outbit

Usage
============

Start the API server on your localhost or on a dedicated IP.  If your using the Docker container then make sure you have pulled the image and have run the image using the above example.

.. sourcecode:: bash

    $ outbit-api -s 127.0.0.1 --insecure

Login to the outbit shell. On the first login you will be prompted to change the default password.  If your using the Docker container you can remove the "--insecure" flag since by default its configured to use ssl.  If you are using valid ssl certificates and not self signed certificates you can also remove the “-–no-check-certificates” flag.

.. sourcecode:: bash

    $ outbit -u superadmin -s 127.0.0.1 --insecure --no-check-certificates
      Password: superadmin
      Changing Password From Default
      Enter New Password: **********
      Enter New Password Again: **********

Example of adding a "hello world" action that prints hello world.

.. sourcecode:: bash

    outbit> help
      actions [list|del|edit|add]
      users [list|del|edit|add]
      roles [list|del|edit|add]
      secrets [list|del|edit|add|encryptpw]
      plugins [list]
      help [*]
      jobs [list|status|kill]
      schedules [add|edit|list|del]
      inventory [list|del]
      ping
      logs
      help
      stats
      exit

    outbit> actions add name=helloworld category=/hello action=world plugin=command desc="print hello world" command_run="echo 'hello world'"

    outbit> help
      actions [list|del|edit|add]
      users [list|del|edit|add]
      roles [list|del|edit|add]
      secrets [list|del|edit|add|encryptpw]
      plugins [list]
      help [*]
      jobs [list|status|kill]
      schedules [add|edit|list|del]
      inventory [list|del]
      ping
      logs
      help
      stats
      hello [world]
      exit

    outbit> hello world
      hello world
      return code: 0

    outbit> exit

License
============
outbit is released under the `MIT License
<./LICENSE.rst>`_.

Author
============
David Whiteside (david@davidwhiteside.com)
