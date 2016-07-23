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
- encryption_password - Encrypt sensitive information in mongodb using this password.  Currently outbit does not support changing the encryption_password after installation.  The password length must be 2^x, for example: 16, 32, and 64 are valid lengths.

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
    encryption_password: "secretencryptpasswordForSecrets"
