#!/bin/bash

service mongodb start

su - outbit -c "outbit-api -s 0.0.0.0"
