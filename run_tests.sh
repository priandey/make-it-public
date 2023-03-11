#!/bin/bash

# Run the Django tests and output coverage report
docker-compose run web sh -c "coverage run --branch manage.py test -v2 --keepdb && coverage report && coverage html --skip-empty"
