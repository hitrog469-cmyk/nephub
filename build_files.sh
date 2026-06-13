#!/bin/bash
# Vercel build step: install deps and gather static files into staticfiles/
pip install -r requirements.txt
python manage.py collectstatic --noinput --clear
