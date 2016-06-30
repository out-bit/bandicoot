Config Files
==================

The search path for the outbit config files is your home directory (~) and then /etc/.  The config file for the outbit CLI is outbit.conf and the API server is outbit-api.conf.

Below are the configuration options available on both the outbit CLI client and API server.

- port
- server
- secure

Below are the configuraiton options only available for the outbit CLI client.

- user
- password
- ssl_verify 

Below are the configuraiton options only available for the outbit API server.

- ssl_key
- ssl_crt

Below shows example config files to use for reference.

.. sourcecode:: bash

    $ cat ~/.outbit.conf
    ---
    port: 8088
    password: secretpassword
    secure: False
    verify: False

    $ cat ~/.outbit-api.conf
    ---
    port: 8088
    server: 127.0.0.1
    secure: False
