# Halcyon Event Ticketing & Seat Reservation API

**Capstone 5 — Advanced Web Development**

| Project Detail | Information |
|---|---|
| Ticket ID | HS-2026-0872 |
| Project | Event Ticketing & Seat Reservation API |
| Backend Framework | Django 5.2 |
| API Framework | Django REST Framework |
| Database | PostgreSQL 16 |
| Authentication | JSON Web Tokens (JWT) |
| Containerisation | Docker and Docker Compose |
| API Documentation | Swagger UI / OpenAPI |
| CI/CD | GitHub Actions |

## 1. Project Overview

The Halcyon Event Ticketing & Seat Reservation API is a Django REST Framework application developed to manage events, venues, seats, bookings and tickets.

The project was developed in response to Capstone 5's requirement to build a production-oriented backend microservice with authentication, role-based permissions, a relational database, containerised deployment, automated testing and continuous integration.

The API uses PostgreSQL to store application data and JWT authentication to protect restricted endpoints. Database constraints and atomic transactions help prevent customers from reserving the same seat more than once.

### Key Features

- User registration, login and JWT token refresh.
- Role-based access for standard users and administrators.
- CRUD operations for supported resources.
- Event, venue, seat and category management.
- Booking creation, viewing and cancellation.
- Seat availability checks and protection against double-booking.
- Standardised JSON error responses.
- Database connectivity and service uptime monitoring.
- Interactive Swagger documentation and an OpenAPI schema.
- Docker-based application and PostgreSQL setup.
- Automated testing, code-quality checks and GitHub Actions CI.

## 2. Technology Stack

- Python 3.12
- Django 5.2
- Django REST Framework
- Simple JWT
- PostgreSQL 16
- drf-spectacular
- Gunicorn
- Docker and Docker Compose
- pytest and pytest-django
- pytest-cov
- Black and Flake8
- GitHub Actions

## 3. Repository

GitHub repository:

https://github.com/Olwethu28/Event-Ticketing-Seat-Reservation-API

The repository contains the Django application, database configuration, Docker configuration, tests, environment template and CI workflow.

## 4. Running the Project Locally

**Important:** This is a backend API, not a hosted website. The reviewer must run the application on their own computer before opening the local API links. The links below use `localhost`, which points to the computer running the application.

### Prerequisites

Install the following:

- [Git](https://git-scm.com/downloads)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/), with Docker Compose available

Start Docker Desktop before proceeding.

### Step 1: Clone the repository

Open a terminal and run:

```bash
git clone https://github.com/Olwethu28/Event-Ticketing-Seat-Reservation-API.git
cd Event-Ticketing-Seat-Reservation-API
```

### Step 2: Create the environment file

Create a local environment file from the supplied template.

For Git Bash:

```bash
cp .env.example .env
```

For Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Review `.env.example` and the project's environment configuration. If any required variables need to be changed, update `.env` using suitable local development values.

Do not commit `.env` or expose database passwords, Django secret keys or other credentials.

### Step 3: Build and start the application

Run:

```bash
docker compose up --build --wait
```

Docker Compose builds the application image, starts the PostgreSQL database and application containers, and waits for the configured health checks.

Keep this terminal open while using the API.

On the first run, the application may need time to build its image and initialise the database.

### Step 4: Verify that the API is running

Open a second terminal and run:

```bash
curl http://localhost:8000/health/
```

A successful response should report that the service is running and the database is connected.

You can also open the health endpoint directly in your browser:

http://localhost:8000/health/

### Step 5: Open the API documentation

Once the application is running, open any of these links in your browser:

| Resource | Local URL |
|---|---|
| Swagger UI — interactive API documentation | http://localhost:8000/api/docs/ |
| OpenAPI schema | http://localhost:8000/api/schema/ |
| Health check | http://localhost:8000/health/ |
| Django administration | http://localhost:8000/admin/ |

**How to use these links:** First start Docker Compose and wait for the application to become available. Then click the link for the resource you want to inspect. Swagger UI allows you to explore the available endpoints and try API requests.

These are local development URLs, not public deployment links. They will work on the computer running the application while the service is available.

### Stopping the application

Press `Ctrl+C` in the terminal running Docker Compose. To stop and remove the Compose containers, run:

```bash
docker compose down
```

The default command preserves the database volume. To delete the stored database data as well, use `docker compose down -v` only when you intentionally want to reset the local database.

## 5. Optional Docker Hub Image

The project image is available at:

**Docker Hub repository:**  
https://hub.docker.com/r/olwethu2/event-ticketing-api

To pull the published image:

```bash
docker pull olwethu2/event-ticketing-api:latest
```

The recommended setup for reviewers is still the Docker Compose procedure above, which builds and starts the application together with PostgreSQL using the repository's configuration.

The Docker Hub image is an additional distribution option. Pulling the image alone does not configure the database or start the complete application.

## 6. Authentication

The API uses JSON Web Token (JWT) authentication.

Users can register and obtain tokens by logging in. Protected endpoints require an access token in the HTTP request header:

```http
Authorization: Bearer <access_token>
```

Access tokens expire after 15 minutes, and refresh tokens expire after one day.

Standard users have access to permitted user operations, while administrative operations are restricted by role-based permissions. Booking access is also subject to ownership permissions.

### Authentication Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/auth/register/` | Register a user |
| POST | `/api/auth/token/` | Obtain JWT tokens |
| POST | `/api/auth/token/refresh/` | Refresh an access token |
| GET | `/api/auth/me/` | Retrieve the authenticated user's profile |

## 7. API Endpoints

The following table summarises the main API routes.

| Resource | Endpoint | Supported operations |
|---|---|---|
| Users | `/api/users/` | List and manage users, subject to permissions |
| Venues | `/api/venues/` | Create, list, retrieve, update and delete |
| Seats | `/api/seats/` | Create, list, retrieve, update and delete |
| Categories | `/api/categories/` | Create, list, retrieve, update and delete |
| Events | `/api/events/` | Create, list, retrieve, update and delete |
| Event seat availability | `/api/events/{id}/available_seats/` | Retrieve available seats |
| Bookings | `/api/bookings/` | Create, list, retrieve, update and delete, subject to permissions |
| Booking cancellation | `/api/bookings/{id}/cancel/` | Cancel a booking |
| Health | `/health/` | Check service and database health |

Exact methods and permissions depend on the endpoint. Consult Swagger UI for the complete request schemas, response formats and available operations.

## 8. Sample cURL Requests

Run these examples after starting the application locally. The examples use fictional account details.

### Set the base URL

In Git Bash or a Linux/macOS terminal:

```bash
export HALCYON_URL=http://localhost:8000
```

### Register a user

```bash
curl --fail-with-body -X POST \
  "$HALCYON_URL/api/auth/register/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "fictional_customer",
    "email": "customer@halcyon.example",
    "password": "Fictional-Customer-0448!"
  }'
```

### Log in and obtain a JWT

```bash
curl --fail-with-body -X POST \
  "$HALCYON_URL/api/auth/token/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "fictional_customer",
    "password": "Fictional-Customer-0448!"
  }'
```

The response contains an access token and a refresh token. Copy the access token for the authenticated requests below.

### Retrieve the current user

Replace `<access_token>` with the access token returned by the login request.

```bash
curl "$HALCYON_URL/api/auth/me/" \
  -H "Authorization: Bearer <access_token>"
```

### Check available seats

Replace `<event_id>` with an existing event ID.

```bash
curl "$HALCYON_URL/api/events/<event_id>/available_seats/" \
  -H "Authorization: Bearer <access_token>"
```

### Create a booking

Replace the example event and seat IDs with valid IDs from your local database.

```bash
curl --fail-with-body -X POST \
  "$HALCYON_URL/api/bookings/" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "event": 1,
    "seats": [1]
  }'
```

### Cancel a booking

Replace `<booking_id>` with the ID of a booking that can be cancelled by the authenticated user.

```bash
curl --fail-with-body -X POST \
  "$HALCYON_URL/api/bookings/<booking_id>/cancel/" \
  -H "Authorization: Bearer <access_token>"
```

These requests demonstrate the API's authentication and booking workflow. For other resources and request bodies, use the interactive Swagger documentation.

## 9. Database Design and Relationships

The application uses related Django models to represent users, events, venues, seats, categories, bookings and tickets.

The relationships connect customers to their bookings, events to their venues and categories, and bookings to the seats and tickets involved in reservations.

Foreign keys and many-to-many relationships support these connections while maintaining referential integrity.

### Database Indexing Strategy

Indexes were selected to support frequently used filtering and lookup operations.

| Index | Reason for the index |
|---|---|
| `event_start_idx` | Improves queries that filter or order events by their start time, such as retrieving upcoming events. |
| `event_venue_start_idx` | Supports queries that filter events by venue and start time. |
| `booking_user_created_idx` | Improves retrieval of a user's booking history, particularly when ordered by creation time. |
| `booking_event_status_idx` | Supports filtering bookings by event and booking status. |

These indexes help PostgreSQL locate relevant records without scanning the entire table for common queries. Composite indexes are most useful when queries use their leading indexed columns in a compatible order.

Indexes also consume storage and add overhead to inserts and updates, so they should support actual query patterns rather than be added indiscriminately.

### Data Integrity and Validation

The database and application enforce appropriate validation and constraints, including:

- Unique usernames and category names.
- Valid seat positions within venues.
- Non-negative event prices.
- Event end times later than event start times.
- Valid user roles and booking statuses.
- Prevention of duplicate seats within a booking.
- Constraints that prevent duplicate active reservations for the same event and seat.

Atomic transactions and PostgreSQL row locking help protect reservation operations against concurrent requests and reduce the risk of double-booking.

## 10. Standardised Error Handling

The API returns structured JSON error responses to make failures easier for clients to interpret.

An example error response is:

```json
{
  "error": {
    "status": 409,
    "code": "conflict",
    "message": "One or more seats are already reserved for this event.",
    "details": {
      "detail": "One or more seats are already reserved for this event."
    },
    "path": "/api/bookings/",
    "timestamp": "2026-10-12T12:00:00+00:00"
  }
}
```

The timestamp above is illustrative.

The API uses appropriate HTTP status codes, including:

- `400` — Invalid request or validation error.
- `401` — Authentication required or invalid credentials.
- `403` — Permission denied.
- `404` — Resource not found.
- `409` — Reservation conflict.
- `500` — Unexpected server error.
- `503` — Service or database unavailable.

Internal database and server details should not be exposed to API clients.

## 11. Health Check

The `/health/` endpoint reports service status, database connectivity and application uptime.

Request:

```bash
curl http://localhost:8000/health/
```

Example successful response:

```json
{
  "service": "halcyon-ticketing-api",
  "status": "ok",
  "database": "connected",
  "uptime_seconds": 42.0
}
```

The uptime value is illustrative and will vary. If the database is unavailable, the endpoint reports degraded service health and returns HTTP `503`.

## 12. Swagger and OpenAPI Documentation

The project uses `drf-spectacular` to generate an OpenAPI schema from the Django REST Framework API.

- **Swagger UI:** http://localhost:8000/api/docs/
- **OpenAPI schema:** http://localhost:8000/api/schema/

Swagger UI allows reviewers to inspect endpoints, view expected request and response formats, and try supported requests against the locally running API.

The schema can also be validated using:

```bash
python manage.py spectacular \
  --file /tmp/halcyon-schema.yml \
  --validate \
  --fail-on-warn
```

Run this command in an environment where the project's Python dependencies and Django settings are configured.

## 13. Testing and Coverage

The project uses `pytest`, `pytest-django` and `pytest-cov`.

The test suite is configured to enforce a minimum code coverage threshold of **80%**.

The tests cover areas including:

- API operations and validation.
- Authentication and permissions.
- Booking ownership and cancellation.
- Model constraints and database behaviour.
- Health checks and API documentation.
- Demo data seeding.
- Concurrent reservation attempts.

Database-backed tests use PostgreSQL to verify transaction behaviour and reservation integrity.

### Run tests

Run the test suite in the configured Python environment:

```bash
pytest
```

To generate a coverage report:

```bash
python -m pytest \
  --cov=config \
  --cov=tickets \
  --cov-report=term-missing \
  --cov-report=xml \
  --cov-fail-under=80
```

The coverage command assumes the development dependencies are installed and the command is executed from the project root.

A successful test run with the coverage threshold enforced demonstrates that the measured code coverage is at least 80%. The actual percentage should be taken from the latest successful test report.

## 14. Code Quality

The project uses Black and Flake8 to check code quality.

Run Black:

```bash
black --check .
```

Run Flake8:

```bash
flake8 .
```

Run Django's system checks:

```bash
python manage.py check
```

Check for uncommitted model migration changes:

```bash
python manage.py makemigrations --check --dry-run
```

## 15. Docker and Containerisation

The project includes a multi-stage `Dockerfile` and a `docker-compose.yml` configuration.

The containerised setup includes:

- A Django application container.
- A PostgreSQL database container.
- Database health checks and persistent database storage.
- Gunicorn as the application server.
- A non-root application user.
- Startup and database initialisation steps.

Build the application image:

```bash
docker build --tag halcyon-ticketing:local .
```

Build and start the complete application:

```bash
docker compose up --build --wait
```

The Compose configuration is the recommended method for local evaluation because it coordinates the application and database services.

## 16. CI/CD Pipeline

The GitHub Actions workflow is located at:

`.github/workflows/ci.yml`

The pipeline automates quality checks and validation when changes are pushed or pull requests are opened.

The configured workflow includes:

1. Code linting and formatting checks.
2. Automated tests against PostgreSQL.
3. OpenAPI schema validation.
4. Docker image building.
5. Docker Compose health verification.

Coverage output is also generated by the testing workflow and uploaded as an artifact when configured by the pipeline.

Workflow runs can be reviewed in the repository's **Actions** tab:

https://github.com/Olwethu28/Event-Ticketing-Seat-Reservation-API/actions

## 17. Demo Data and Administration

The project includes an optional command for creating fictional demonstration data.

Run it after starting the application:

```bash
docker compose exec \
  -e DEMO_PASSWORD='Fictional-Seeding-0448!' \
  app python manage.py seed_demo
```

This command creates demonstration records such as users, a venue, seats, a category and an event.

The password shown is an example for local demonstration only. Use an appropriate local value and do not reuse it for real accounts.

To create a Django administrator account:

```bash
docker compose exec app python manage.py createsuperuser
```

The Django administration interface is available at:

http://localhost:8000/admin/

## 18. Project Deliverables

| Deliverable | Link or Location |
|---|---|
| GitHub repository | https://github.com/Olwethu28/Event-Ticketing-Seat-Reservation-API |
| Docker Hub image | https://hub.docker.com/r/olwethu2/event-ticketing-api |
| CI/CD workflow | `.github/workflows/ci.yml` |
| Swagger UI | `http://localhost:8000/api/docs/` after starting the application |
| OpenAPI schema | `http://localhost:8000/api/schema/` after starting the application |
| Health endpoint | `http://localhost:8000/health/` after starting the application |
| README | `README.md` in the repository |

## 19. Running the Project for Assessment

To evaluate this project locally:

1. Clone the GitHub repository.
2. Start Docker Desktop.
3. Create the `.env` file from `.env.example`.
4. Run `docker compose up --build --wait`.
5. Confirm that the health endpoint reports a healthy service.
6. Open Swagger UI to inspect and test the API.
7. Review the CI workflow and test reports to verify the automated checks and coverage.

**Note:** The localhost links are available only while the application is running on the reviewer's computer. A public deployment is not implied by these local URLs.

