#!/bin/bash
shopt -s expand_aliases
source ~/.profile
# Run the Django tests and output coverage report
docker-compose run web sh -c "coverage run --branch manage.py test -v2 --keepdb && coverage report && coverage html --skip-empty"
