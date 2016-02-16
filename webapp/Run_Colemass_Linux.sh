#!/bin/bash
python manage.py celery worker &
python manage.py runserver 0:8000 &
