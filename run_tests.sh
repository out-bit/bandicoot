#!/bin/bash
export PYTHONPATH="${PYTHONPATH}:./lib"
coverage run --source=bandicoot $(which nosetests) -w test/units/
