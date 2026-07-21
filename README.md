# Ntando's News

## Overview

Ntando's News is a Django-based news management application that demonstrates role-based access control, REST API development, JWT authentication, publisher management, article approval workflows, newsletter creation, and MariaDB integration.

The application allows:

- Readers to browse approved news articles and newsletters.
- Journalists to create articles and newsletters.
- Editors to review and approve articles.
- Publishers to manage their assigned journalists and editors.

The project was developed using Django, Django REST Framework, MariaDB, and Simple JWT.

---

# Features

## Reader

Readers can:

- Register an account
- Log in securely
- View approved articles
- View newsletters
- Subscribe to journalists
- Subscribe to publishers
- Receive approved articles by email
- View personalised subscribed content

---

## Journalist

Journalists can:

- Create independent articles
- Create articles for publishers they are assigned to
- Edit their own articles
- Delete their own articles
- Create newsletters
- Add approved articles to newsletters
- Manage articles through the REST API

---

## Editor

Editors can:

- Review pending articles
- Approve articles
- Manage approved articles
- Manage newsletters
- Approve publisher articles only if assigned to that publisher

---

## Publisher

Publishers can have:

- Multiple journalists
- Multiple editors

Only:

- Assigned journalists can publish articles for that publisher.
- Assigned editors can approve articles for that publisher.

---

# Technologies Used

- Python 3
- Django
- Django REST Framework
- Simple JWT
- MariaDB
- PyMySQL
- Requests
- python-dotenv
- HTML
- CSS

---

# Clone the Project

```powershell
git clone https://github.com/ntando1227/ntandos_news.git

cd ntandos_news
```

---

# Create a Virtual Environment

```powershell
py -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

---

# Install Dependencies

```powershell
py -m pip install --upgrade pip

pip install -r requirements.txt
```

---

# MariaDB Setup

This project uses **MariaDB** instead of SQLite.

Download the MariaDB ZIP package from:

https://mariadb.org/download/

Extract it anywhere on your computer.

Example:

```text
C:\path\to\mariadb-12.3.2-winx64
```

Replace the example path with the location where you extracted MariaDB.

---

## Configure MariaDB

Open PowerShell.

```powershell
$MariaDbHome = "C:\path\to\mariadb-12.3.2-winx64"

$DataDir = "$HOME\Documents\ntandos_news_mariadb_data"
```

Create the data directory.

```powershell
New-Item -ItemType Directory -Path $DataDir -Force
```

---

## Initialise MariaDB

```powershell
& "$MariaDbHome\bin\mariadb-install-db.exe" `
    --datadir="$DataDir" `
    --password="YourRootPassword" `
    --port=3307
```

---

## Start MariaDB

```powershell
& "$MariaDbHome\bin\mariadbd.exe" `
    --console `
    --basedir="$MariaDbHome" `
    --datadir="$DataDir" `
    --port=3307 `
    --bind-address=127.0.0.1
```

Keep this PowerShell window open.

---

## Create the Database

Open another PowerShell window.

```powershell
$MariaDbHome = "C:\path\to\mariadb-12.3.2-winx64"
```

```powershell
@"
CREATE DATABASE ntandos_news_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

CREATE USER 'ntando_news_user'@'localhost'
IDENTIFIED BY 'ChooseASecurePassword';

GRANT ALL PRIVILEGES ON ntandos_news_db.*
TO 'ntando_news_user'@'localhost';

FLUSH PRIVILEGES;
"@ | & "$MariaDbHome\bin\mariadb.exe" `
    --host=127.0.0.1 `
    --port=3307 `
    --user=root `
    --password
```

---

# Environment Variables

Copy the example file.

```powershell
Copy-Item .env.example .env
```

Edit `.env`.

```text
DJANGO_SECRET_KEY=replace-with-a-secret-key

DJANGO_DEBUG=True

DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=ntandos_news_db

DB_USER=ntando_news_user

DB_PASSWORD=ChooseASecurePassword

DB_HOST=127.0.0.1

DB_PORT=3307

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

DEFAULT_FROM_EMAIL=ntandosnews@example.com
```

---

# Apply Migrations

```powershell
py manage.py migrate
```

---

# Create a Superuser

```powershell
py manage.py createsuperuser
```

---

# Run the Server

```powershell
py manage.py runserver
```

Open:

```
http://127.0.0.1:8000/
```

Admin:

```
http://127.0.0.1:8000/admin/
```

---

# Publisher Management

Publishers are managed through Django Admin.

Administrators can:

- Create publishers
- Assign journalists
- Assign editors

Business rules:

- Journalists can only create articles for publishers they are assigned to.
- Editors can only approve publisher articles belonging to publishers they are assigned to.
- Independent articles can still be created.

---

# Article Approval

When an editor approves an article:

- The article becomes publicly visible.
- Subscribers to the journalist receive an email.
- Subscribers to the publisher receive an email.
- The approval is recorded through the Approved Articles API.
- If the API call fails, a local approval log is created.

---

# REST API

## Authentication

```
POST /api/token/
POST /api/token/refresh/
```

---

## Articles

```
GET     /api/articles/
POST    /api/articles/
GET     /api/articles/<id>/
PUT     /api/articles/<id>/
PATCH   /api/articles/<id>/
DELETE  /api/articles/<id>/
```

---

## Subscribed Articles

```
GET /api/articles/subscribed/
```

---

## Publishers

```
GET /api/publishers/
GET /api/publishers/<id>/
```

---

## Newsletters

```
GET     /api/newsletters/
POST    /api/newsletters/
GET     /api/newsletters/<id>/
PUT     /api/newsletters/<id>/
PATCH   /api/newsletters/<id>/
DELETE  /api/newsletters/<id>/
```

---

## Approved Articles

```
GET  /api/approved/
POST /api/approved/
```

---

# Testing

Run the automated test suite.

```powershell
py manage.py test newsapp --verbosity 2
```

Expected output:

```
Ran 24 tests

OK
```

---

# Project Structure

```
ntandos_news/

│── manage.py

│── README.md

│── requirements.txt

│── .env.example

│── .gitignore

│

├── ntandos_news/

│ ├── settings.py

│ ├── urls.py

│ ├── asgi.py

│ └── wsgi.py

│

├── newsapp/

│ ├── admin.py

│ ├── apps.py

│ ├── forms.py

│ ├── models.py

│ ├── permissions.py

│ ├── serializers.py

│ ├── signals.py

│ ├── tests.py

│ ├── urls.py

│ ├── views.py

│ └── web_views.py

│

├── templates/

│

└── static/
```

---

# Security

- Passwords are securely hashed by Django.
- JWT protects API authentication.
- Database credentials are stored in `.env`.
- `.env` is excluded from Git.
- Role-based permissions protect application resources.
- Publisher assignment rules are enforced.

---

# Author

**Ntando Mtimkulu**

Software Engineering Student

Introduction to Software Engineering Capstone Project