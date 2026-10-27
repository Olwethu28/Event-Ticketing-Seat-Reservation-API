# Halcyon Event Ticketing & Seat Reservation API

A production-oriented Django REST API for event ticketing and seat reservations, developed for **Capstone 5 — Advanced Web Development**.

**Ticket:** HS-2026-0872  
**System:** Event Ticketing & Seat Reservation API

## Overview

This project provides an authenticated REST API for managing:

- Users and roles
- Venues
- Seats
- Events
- Categories
- Bookings
- Tickets

The API uses JWT authentication, role-based permissions, PostgreSQL, Docker, automated testing, and GitHub Actions CI.

The system is designed to prevent double-booking through database constraints and atomic transactions.

---

## Tech Stack

- **Python 3.12**
- **Django 5.2**
- **Django REST Framework**
- **SimpleJWT**
- **PostgreSQL 16**
- **drf-spectacular / OpenAPI**
- **Gunicorn**
- **Docker & Docker Compose**
- **pytest / pytest-django**
- **Black**
- **Flake8**
- **GitHub Actions**

---

## Features

### Authentication and Permissions

- JWT authentication
- User registration
- Login and token refresh
- Standard users and administrators
- Role-based permissions
- Ownership-based access to bookings
- Protected administrative operations

### Event Management

Administrators can create, update and delete:

- Venues
- Seats
- Events
- Categories
- Users

Authenticated users can view available events and seats.

### Booking Management

Users can:

- Create bookings
- View their bookings
- Cancel bookings
- Reserve multiple seats
- View available seats

The system prevents double-booking using:

- Database constraints
- Atomic transactions
- PostgreSQL row locking
- Partial unique constraints

---

## Project Structure

```text
django-api/
├── .github/
│   └── workflows/
│       └── ci.yml
├── accounts/
├── bookings/
├── events/
├── config/
├── tests/
├── Dockerfile
├── docker-compose.yml
├── manage.py
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
├── .flake8
├── pyproject.toml
├── .env.example
└── README.md
```

---

# Getting Started

## Prerequisites

Install:

- Docker
- Docker Compose v2
- Git

---

## Run with Docker Compose

Clone the repository:

```bash
git clone https://github.com/Olwethu28/Event-Ticketing-Seat-Reservation-API.git
cd Event-Ticketing-Seat-Reservation-API
```

Create the environment file:

```bash
cp .env.example .env
```

Start the application:

```bash
docker compose up --build --wait
```

Check the health endpoint:

```bash
curl --fail http://localhost:8000/health/
```

The API should now be available at:

```text
http://localhost:8000
```

---

## Demo Data

Optional fictional demo data can be created with:

```bash
docker compose exec -e DEMO_PASSWORD='Fictional-Seeding-0448!' app \
python manage.py seed_demo
```

The command creates fictional users, a venue, seats, category and event.

To create a Django superuser:

```bash
docker compose exec app python manage.py createsuperuser
```

---

# Authentication

The API uses JWT authentication.

Authenticated requests must include:

```http
Authorization: Bearer <access_token>
```

Access tokens expire after 15 minutes and refresh tokens expire after one day.

Registration creates standard users. Administrative privileges can only be managed by authorised administrators.

---

# API Endpoints

| Endpoint | Methods | Access |
|---|---|---|
| `/api/auth/register/` | POST | Public |
| `/api/auth/token/` | POST | Public |
| `/api/auth/token/refresh/` | POST | Public |
| `/api/auth/me/` | GET, PUT, PATCH | Authenticated |
| `/api/users/` | GET, POST, PUT, PATCH, DELETE | Admin |
| `/api/venues/` | GET, POST, PUT, PATCH, DELETE | Authenticated/Admin |
| `/api/seats/` | GET, POST, PUT, PATCH, DELETE | Authenticated/Admin |
| `/api/categories/` | GET, POST, PUT, PATCH, DELETE | Authenticated/Admin |
| `/api/events/` | GET, POST, PUT, PATCH, DELETE | Authenticated/Admin |
| `/api/events/{id}/available_seats/` | GET | Authenticated |
| `/api/bookings/` | GET, POST, PUT, PATCH, DELETE | Authenticated |
| `/api/bookings/{id}/cancel/` | POST | Authenticated |
| `/health/` | GET | Public |
| `/api/schema/` | GET | Public |
| `/api/docs/` | GET | Public |

---

# cURL Examples

Set the API URL:

```bash
export HALCYON_URL=http://localhost:8000
```

## Register a User

```bash
curl --fail-with-body -X POST "$HALCYON_URL/api/auth/register/" \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "fictional_customer",
    "email": "customer@halcyon.example",
    "password": "Fictional-Customer-0448!"
  }'
```

## Login

```bash
curl --fail-with-body -X POST "$HALCYON_URL/api/auth/token/" \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "fictional_customer",
    "password": "Fictional-Customer-0448!"
  }'
```

The response contains an access token that can be used for authenticated requests.

## Get Current User

```bash
curl "$HALCYON_URL/api/auth/me/" \
  -H "Authorization: Bearer <access_token>"
```

## Check Available Seats

```bash
curl "$HALCYON_URL/api/events/<event_id>/available_seats/" \
  -H "Authorization: Bearer <access_token>"
```

## Create a Booking

```bash
curl -X POST "$HALCYON_URL/api/bookings/" \
  -H "Authorization: Bearer <access_token>" \
  -H 'Content-Type: application/json' \
  -d '{
    "event": 1,
    "seats": [1]
  }'
```

## Cancel a Booking

```bash
curl -X POST "$HALCYON_URL/api/bookings/<booking_id>/cancel/" \
  -H "Authorization: Bearer <access_token>"
```

---

# Health Check

The `/health/` endpoint checks database connectivity and reports service status and uptime.

```bash
curl http://localhost:8000/health/
```

Successful response:

```json
{
  "service": "halcyon-ticketing-api",
  "status": "ok",
  "database": "connected",
  "uptime_seconds": 42.0
}
```

If the database is unavailable, the endpoint returns HTTP `503` with a degraded service status.

---

# Swagger / OpenAPI Documentation

Interactive Swagger documentation:

```text
http://localhost:8000/api/docs/
```

OpenAPI schema:

```text
http://localhost:8000/api/schema/
```

The schema can be validated with:

```bash
python manage.py spectacular \
  --file /tmp/halcyon-schema.yml \
  --validate \
  --fail-on-warn
```

---

# Testing

The project uses **pytest** and **pytest-django**.

Run the test suite:

```bash
pytest
```

The project enforces a minimum test coverage of **80%**.

Coverage is generated using `pytest-cov`.

The tests cover:

- API CRUD operations
- Authentication
- Permissions
- Booking ownership
- Booking cancellation
- Database constraints
- Health endpoint
- API documentation
- Demo data seeding
- Concurrent reservation attempts

The database-backed tests use PostgreSQL to verify transaction behaviour and double-booking prevention.

---

# Code Quality

The project uses Black and Flake8 for code quality.

Run Black:

```bash
black --check .
```

Run Flake8:

```bash
flake8 .
```

Run Django checks:

```bash
python manage.py check
```

Check for migration changes:

```bash
python manage.py makemigrations --check --dry-run
```

---

# Docker

The application uses a multi-stage Dockerfile.

The Docker setup includes:

- Application container
- PostgreSQL database container
- Health checks
- Persistent PostgreSQL volume
- Gunicorn
- Non-root application user

Build the image:

```bash
docker build --tag halcyon-ticketing:local .
```

Start the complete application:

```bash
docker compose up --build --wait
```

---

# CI/CD Pipeline

GitHub Actions is configured in:

```text
.github/workflows/ci.yml
```

The pipeline performs:

```text
Lint
  ↓
PostgreSQL tests
  ↓
Schema validation
  ↓
Docker image build
  ↓
Docker Compose health check
```

The pipeline runs on pushes and pull requests.

Coverage is also generated during CI and uploaded as an artifact.

---

# Database Design

The project contains multiple related models using foreign-key and many-to-many relationships.

Key relationships include:

```text
User
 └── Booking
      ├── Event
      │    ├── Venue
      │    │    └── Seat
      │    └── Category
      └── Ticket
           └── Seat
```

The database uses indexes and constraints to improve query performance and protect data integrity.

## Important Indexes

| Index | Purpose |
|---|---|
| `event_start_idx` | Speeds up upcoming event queries |
| `event_venue_start_idx` | Speeds up venue-specific event queries |
| `booking_user_created_idx` | Speeds up user booking history queries |
| `booking_event_status_idx` | Speeds up event booking-status queries |

## Important Constraints

- Unique username
- Unique category names
- Unique venue seat positions
- Valid seat numbers
- Non-negative prices
- Event end time after start time
- Valid user roles
- Valid booking statuses
- Prevention of duplicate active tickets
- Prevention of duplicate seats within a booking

A partial unique constraint on active tickets prevents two customers from reserving the same seat for the same event.

---

# Error Handling

API errors use a standardised JSON structure:

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

The API uses appropriate HTTP status codes:

- `400` — Validation error
- `401` — Authentication required
- `403` — Permission denied
- `404` — Resource not found
- `409` — Conflict
- `500` — Unexpected server error
- `503` — Database/service unavailable

Internal database and server details are not exposed to API clients.

---

# Submission

**GitHub Repository**

https://github.com/Olwethu28/Event-Ticketing-Seat-Reservation-API.git

**CI Pipeline**

```text
.github/workflows/ci.yml
```

**Swagger UI**

```text
/api/docs/
```

**OpenAPI Schema**

```text
/api/schema/
```

**DockerHub**

DockerHub publishing is optional and is not currently configured.

---

## Project Status

The project is designed to satisfy the Capstone 5 requirements for an authenticated, containerised Django REST microservice with PostgreSQL, automated testing, API documentation and CI/CD.