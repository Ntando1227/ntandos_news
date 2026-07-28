# Ntando's News

Ntando's News is a Django-based news management platform that allows journalists to create articles, editors to approve them, publishers to manage content, and readers to subscribe to updates.

## Running the project locally with a virtual environment

### Step 1: Clone the repository

    git clone https://github.com/Ntando1227/ntandos_news.git
    cd ntandos_news

### Step 2: Create a virtual environment

    py -m venv venv

### Step 3: Activate the virtual environment

    .\venv\Scripts\Activate.ps1

### Step 4: Install dependencies

    pip install -r requirements.txt

### Step 5: Create the environment file

    Copy-Item .env.example .env

Update the database credentials in .env.

For local development, use:

    DB_HOST=127.0.0.1
    DB_PORT=3307

Ensure that MariaDB is running before continuing.

### Step 6: Apply migrations

    py manage.py migrate

### Step 7: Create a superuser

    py manage.py createsuperuser

### Step 8: Start the server

    py manage.py runserver

Open the application in your browser:

    http://127.0.0.1:8000/

Open the Django administration site:

    http://127.0.0.1:8000/admin/

## Running with Docker Compose

The Docker configuration runs Django and MariaDB in separate containers.

The Django container connects to MariaDB using:

    DB_HOST=db
    DB_PORT=3306

The value db matches the MariaDB service name in docker-compose.yml.

### Step 1: Build and start the containers

    docker compose up --build

Docker Compose will:

- build the Django image;
- download the MariaDB image;
- start both containers;
- wait for MariaDB to become healthy;
- apply database migrations;
- start the Django development server.

### Step 2: Open the application

Open:

    http://127.0.0.1:8000/

### Step 3: Create a superuser inside Docker

Open another terminal in the project folder and run:

    docker compose exec web python manage.py createsuperuser

### Step 4: Stop the containers

Press Ctrl + C in the Docker Compose terminal, then run:

    docker compose down

To remove the Docker database volume as well, run:

    docker compose down -v

## Automated tests

    py manage.py test newsapp --verbosity 2

## Sphinx documentation

Rebuild the documentation with:

    .\docs\make.bat html

The generated documentation is available at:

    docs/build/html/index.html

## Public repository

https://github.com/Ntando1227/ntandos_news

## Docker verification

The Docker Compose configuration was tested in GitHub Codespaces.

Both services started successfully:

- MariaDB database container reported healthy.
- Django web container started and exposed port 8000.
- The web application was accessible through the Codespaces forwarded port.
