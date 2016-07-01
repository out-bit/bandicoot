#!/bin/bash

service mongodb start

groupadd -r outbit && useradd -r -g outbit outbit

touch /var/log/outbit.log
chmod 755 /var/log/outbit.log
chown outbit: /var/log/outbit.log

su - outbit -c "outbit-api -s 0.0.0.0"
