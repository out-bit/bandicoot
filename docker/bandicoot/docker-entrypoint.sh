#!/bin/bash

service mongodb start
service nginx start

su - bandicoot -c "bandicoot-api"
