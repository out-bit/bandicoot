Config Files
==================

The search path for the outbit config files is your home directory (~/.outbit.conf, ~/.outbit-api.conf) and then /etc/ (/etc/outbit.conf, /etc/outbit-api.conf).  The config file for the outbit CLI is outbit.conf and the API server is outbit-api.conf.

Below are the configuration options available on both the outbit CLI client and API server.

- port - Tcp port to connect (client) or listen on (server).
- server - IP address or hostname of server to connect to (client) or the server listen address (server).
- secure - Encrypt communication using https. This is to prevent passwords being transfmitted clear text over the network.

Below are the configuraiton options only available for the outbit CLI client.

- user - User login name.
- password - User login password.
- ssl_verify  - Verify the ssl certificate of the server is valid. This is to protect against man-in-the-middle attacks.

Below are the configuration options only available for the outbit API server.

- ssl_key - Private SSL key to use.
- ssl_crt - Public SSL key to use.
- encryption_password - Encrypt sensitive information in mongodb using this password. If you change this password after adding secrets, use 'secrets encryptpw oldpw=XXXX' to migrate secrets to the new password.

Below shows example config files to use for reference.

.. sourcecode:: bash

    $ cat ~/.outbit.conf
    ---
    port: 8088
    password: secretpassword
    secure: False
    ssl_verify: False

    $ cat ~/.outbit-api.conf
    ---
    port: 8088
    server: 127.0.0.1
    secure: False
    encryption_password: "secretencryptpasswordForSecrets"

    $ cat /etc/outbit.conf
    ---
    port: 8088
    server: 192.168.1.100
    password: secretpassword
    secure: True
    ssl_verify: True

    $ cat /etc/outbit-api.conf
    ---
    port: 8088
    server: 0.0.0.0
    secure: True
    encryption_password: "secretencryptpasswordForSecrets"
