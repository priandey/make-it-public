#!/bin/bash
shopt -s expand_aliases
source ~/.profile
# Run the Django tests and output coverage report
docker-compose run web python manage.py "$@"
