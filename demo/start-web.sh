#!/bin/sh
set -eu

python manage.py seed_demo_once
exec gunicorn ibsec_lms.wsgi:application --config /app/docker/gunicorn.conf.py
