#!/bin/bash
export PYTHONPATH="${PYTHONPATH}:./lib"
coverage run --source=outbit $(which nosetests) -w test/units/
