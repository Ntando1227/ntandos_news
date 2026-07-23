# Ntando's News

Ntando's News is a Django capstone project.

## Features

- Reader, Journalist, and Editor roles
- Article creation, editing, approval, and deletion
- Newsletter creation, editing, and deletion
- Publisher creation and management
- Reader subscriptions
- REST API with JWT authentication
- MariaDB configuration
- Automated tests
- Sphinx documentation
- Docker support

## Project structure

ntandos_news/
manage.py
requirements.txt
README.md
Dockerfile
docker-compose.yml
capstone.txt
.gitignore
.dockerignore
.env.example
newsapp/
ntandos_news/
templates/
static/
docs/

## Run locally

py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
py manage.py migrate
py manage.py runserver

## Run tests

py manage.py test newsapp --verbosity 2

## Docker

docker build -t ntandos-news:latest .
docker compose up --build

## Repository

https://github.com/Ntando1227/ntandos_news
