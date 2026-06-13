#!/bin/bash
# Vercel build step: install deps and gather static files into staticfiles/
# Vercel's build image uses a uv-managed Python (PEP 668), so pip needs
# --break-system-packages to install into it.
set -e
python3 -m pip install --break-system-packages -r requirements.txt
python3 manage.py collectstatic --noinput --clear
