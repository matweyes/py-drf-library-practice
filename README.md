# Library Service API

RESTful backend for an online library management system.
Handles book inventory, user borrowings, and payments tracking — replacing the library's outdated paper-based workflow.

## Tech Stack

- **Python 3.12**
- **Django 6.1** — web framework
- **Django REST Framework 3.18** — API toolkit
- **PostgreSQL 16** — database
- **JWT** (`djangorestframework-simplejwt`) — authentication
- **drf-spectacular** — OpenAPI 3 schema + Swagger / ReDoc
- **Docker & Docker Compose** — containerized deployment
- **Poetry** — dependency management

## API Endpoints

### Users

| Method      | Endpoint                   | Description                    | Auth     |
|-------------|----------------------------|--------------------------------|----------|
| `POST`      | `/api/users/`              | Register a new user            | —        |
| `POST`      | `/api/users/token/`        | Obtain JWT access + refresh    | —        |
| `POST`      | `/api/users/token/refresh/`| Refresh an expired access token| —        |
| `GET`       | `/api/users/me/`           | Retrieve own profile           | Required |
| `PUT/PATCH` | `/api/users/me/`           | Update own profile             | Required |

### Documentation

| Endpoint               | Description          |
|------------------------|----------------------|
| `/api/doc/swagger/`    | Swagger UI           |
| `/api/doc/redoc/`      | ReDoc                |
| `/api/schema/`         | OpenAPI 3 schema     |

## Getting Started

### Prerequisites

- Python 3.12+
- Poetry 2.x

### Installation

```shell
git clone <repo-url>
cd drf-library-practice
poetry install
```

### Configuration

Copy `.env.sample` to `.env` and adjust values:

```shell
cp .env.sample .env
```

| Variable               | Description                     | Default                   |
|------------------------|---------------------------------|---------------------------|
| `POSTGRES_DB`          | Database name                   | `library`                 |
| `POSTGRES_USER`        | Database user                   | `library`                 |
| `POSTGRES_PASSWORD`    | Database password               | `library`                 |
| `POSTGRES_HOST`        | Database host                   | `localhost`               |
| `POSTGRES_PORT`        | Database port                   | `5432`                    |
| `DJANGO_SECRET_KEY`    | Django secret key               | (insecure dev default)    |
| `DJANGO_DEBUG`         | Set to `False` for production   | `True`                    |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed hosts   | `localhost,127.0.0.1`     |
| `USE_SQLITE`           | Use SQLite instead of Postgres  | (unset = Postgres)        |

### Running Locally (SQLite)

```shell
USE_SQLITE=True poetry run python manage.py migrate
USE_SQLITE=True poetry run python manage.py runserver
```

### Running Tests

```shell
USE_SQLITE=True poetry run python manage.py test --verbosity=2
```
