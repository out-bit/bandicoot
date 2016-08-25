#!/bin/bash

service mongodb start
service nginx start

su - outbit -c "outbit-api"
