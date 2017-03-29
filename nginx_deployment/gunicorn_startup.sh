#!/bin/bash
source /Users/django/.virtualenvs/bcpp/bin/activate && cd /Users/django/source/bcpp && gunicorn -c gunicorn.conf.py bcpp.wsgi --pid /Users/django/source/bcpp/logs/gunicorn.pid --deamon