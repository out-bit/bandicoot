Getting Started with bandicoot
==================

Installing bandicoot client

.. sourcecode:: bash

    $ pip install bandicoot

Installing bandicoot api server

.. sourcecode:: bash

  $ pip install bandicoot
  $ sudo bandicoot-api-install

Starting the bandicoot api server.

.. sourcecode:: bash

    $ bandicoot-api -s 127.0.0.1 --insecure

Installing and Starting the bandicoot api server using Docker.

.. sourcecode:: bash

  $ docker pull starboarder2001/bandicoot
  $ docker run -d -p 8088:8088 -p 80:80 -p 443:443 starboarder2001/bandicoot

Login to the bandicoot shell. On the first login you will be prompted to change the default password.  If your using the Docker container you can remove the "--insecure" flag since by its configured to use ssl.  If you are using valid ssl certificates and not self signed certificates you can also remove the "--no-check-certificates" flag.

.. sourcecode:: bash

    $ bandicoot -u superadmin -s 127.0.0.1 --insecure --no-check-certificates
      Password: superadmin
      Changing Password From Default
      Enter New Password: **********
      Enter New Password Again: **********

outit CLI Basics

The help command will display all the commands available to run.

.. sourcecode:: bash

    bandicoot> help
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

    bandicoot> exit

The logs command will display the history of actions performed.

.. sourcecode:: bash

    bandicoot> logs

bandicoot CLI Non-Interactive Usage

You can run commands with bandicoot from the bash shell without entering the interactive bandicoot shell.

.. sourcecode:: bash

    $ bandicoot 'logs'
      Password: ******
      superadmin    /       ping    None    06/18/2016 09:19
      superadmin    /       ping    None    06/18/2016 09:19
      superadmin    /       help    None    06/18/2016 09:19

    $ bandicoot 'logs' 'users list'
      Password: ******
      superadmin    /       ping    None    06/18/2016 09:19
      superadmin    /       ping    None    06/18/2016 09:19
      superadmin

If you do not wish to type the password for each login attempt, you can set your password in the bandicoot configuration file.

.. sourcecode:: bash
    $ echo "---" > ~/.bandicoot.conf
    $ echo "password: *****" >> ~/.bandicoot.conf
    $ bandicoot 'logs'
      superadmin    /       ping    None    06/18/2016 09:19
      superadmin    /       ping    None    06/18/2016 09:19
      superadmin    /       help    None    06/18/2016 09:19
