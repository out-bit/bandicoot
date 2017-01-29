Getting Started with outbit
==================

Installing outbit client

.. sourcecode:: bash

    $ pip install outbit

Installing outbit api server

.. sourcecode:: bash

  $ pip install outbit
  $ sudo outbit-api-install

Starting the outbit api server.

.. sourcecode:: bash

    $ outbit-api -s 127.0.0.1 --insecure

Installing and Starting the outbit api server using Docker.

.. sourcecode:: bash

  $ docker pull starboarder2001/outbit
  $ docker run -d -p 8088:8088 -p 80:80 -p 443:443 starboarder2001/outbit

Login to the outbit shell. On the first login you will be prompted to change the default password.  If your using the Docker container you can remove the "--insecure" flag since by its configured to use ssl.  If you are using valid ssl certificates and not self signed certificates you can also remove the "--no-check-certificates" flag.

.. sourcecode:: bash

    $ outbit -u superadmin -s 127.0.0.1 --insecure --no-check-certificates
      Password: superadmin
      Changing Password From Default
      Enter New Password: **********
      Enter New Password Again: **********

outit CLI Basics

The help command will display all the commands available to run.

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

The exit command will exit the application.

.. sourcecode:: bash

    outbit> exit

The logs command will display the history of actions performed.

.. sourcecode:: bash

    outbit> logs

outbit CLI Non-Interactive Usage

You can run commands with outbit from the bash shell without entering the interactive outbit shell.

.. sourcecode:: bash

    $ outbit 'logs'
      Password: ******
      superadmin    /       ping    None    06/18/2016 09:19
      superadmin    /       ping    None    06/18/2016 09:19
      superadmin    /       help    None    06/18/2016 09:19

    $ outbit 'logs' 'users list'
      Password: ******
      superadmin    /       ping    None    06/18/2016 09:19
      superadmin    /       ping    None    06/18/2016 09:19
      superadmin

If you do not wish to type the password for each login attempt, you can set your password in the outbit configuration file.

.. sourcecode:: bash
    $ echo "---" > ~/.outbit.conf
    $ echo "password: *****" >> ~/.outbit.conf
    $ outbit 'logs'
      superadmin    /       ping    None    06/18/2016 09:19
      superadmin    /       ping    None    06/18/2016 09:19
      superadmin    /       help    None    06/18/2016 09:19
