#!/bin/bash

# Apply database migrations
python manage.py makemigrations core
python manage.py migrate
python manage.py populate_default

# Start the Django development server
python manage.py runserver 0.0.0.0:8000