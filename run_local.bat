@echo off
cd /d %~dp0
if not exist .venv python -m venv .venv
call .venv\Scripts\activate
python -m pip install -r requirements.txt
if not exist .env copy .env.example .env
python manage.py migrate
python manage.py seed_departments
python manage.py runserver 127.0.0.1:8000
