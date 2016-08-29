#!/bin/bash

service mongodb start
service nginx start

su - outbit -c "outbit-api -s 0.0.0.0"
