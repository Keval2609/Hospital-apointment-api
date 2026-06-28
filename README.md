# Hospital Appointment API

A production-ready REST API for managing hospital appointments, built with **FastAPI**, **PostgreSQL**, **SQLAlchemy 2.0**, and **JWT authentication**.

## Architecture

```
┌────────────────────────────────────────────────────┐
│                    API Layer                       │
│          (FastAPI routes + validation)             │
├────────────────────────────────────────────────────┤
│                  Service Layer                     │
│          (Business logic + orchestration)          │
├────────────────────────────────────────────────────┤
│                Repository Layer                    │
│        (Data access + query abstraction)           │
├────────────────────────────────────────────────────┤
│               SQLAlchemy 2.0 ORM                   │
│            (Async engine + models)                 │
├────────────────────────────────────────────────────┤
│                  PostgreSQL                        │
└────────────────────────────────────────────────────┘
```

**Key Principles:**
- Clean Architecture with clear layer separation
- Repository Pattern for data access abstraction
- Dependency Injection via FastAPI's `Depends`
- SOLID principles throughout

## Tech Stack

| Technology        | Version  | Purpose                    |
|-------------------|----------|----------------------------|
| Python            | 3.12+    | Runtime                    |
| FastAPI           | 0.115+   | Web framework              |
| PostgreSQL        | 16+      | Database                   |
| SQLAlchemy        | 2.0+     | ORM (async)                |
| Alembic           | 1.15+    | Database migrations        |
| Pydantic          | 2.11+    | Validation & schemas       |
| python-jose       | 3.4+     | JWT tokens                 |
| passlib + bcrypt  | 1.7+     | Password hashing           |
| pytest            | 8.3+     | Testing                    |

## Features

- **Authentication**: Register, Login, Refresh Token, Logout
- **Authorization**: Role-Based Access Control (Admin, Doctor, Patient)
- **User Management**: Full CRUD (admin-only)
- **Doctor Profiles**: CRUD with specialty & availability filters
- **Patient Profiles**: CRUD with ownership-based access control
- **Pagination**: Consistent paginated responses across all list endpoints
- **Validation**: Pydantic v2 request/response validation
- **Error Handling**: Structured JSON error responses with error codes
- **Logging**: Structured request logging with correlation IDs
- **API Docs**: Interactive Swagger UI and ReDoc

## Project Structure

```
Hospital_appointment_api/
├── alembic/                # Database migrations
├── app/
│   ├── api/v1/             # Route handlers
│   ├── core/               # Security, enums
│   ├── models/             # SQLAlchemy models
│   ├── repositories/       # Data access layer
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic
│   ├── config.py           # Settings
│   ├── database.py         # DB engine & session
│   ├── dependencies.py     # DI wiring
│   ├── exceptions.py       # Custom exceptions
│   ├── exception_handlers.py
│   ├── middleware.py        # Logging, CORS, correlation ID
│   └── main.py             # App factory
└── tests/                  # Test suite
```

## Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL 16+
- pip or uv

### 1. Clone & Install

```bash
git clone <repository-url>
cd Hospital_appointment_api

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -e ".[dev]"
```

### 2. Configure Environment

```bash
copy .env.example .env
# Edit .env with your PostgreSQL credentials
```

### 3. Create Database

You need to create the PostgreSQL database. If you have the `psql` command-line tool installed, you can run this in your terminal:

```bash
psql -U postgres -c "CREATE DATABASE hospital_db;"
```

Alternatively, you can use a GUI tool like **pgAdmin** or **DBeaver** to create a database named `hospital_db`.

### 4. Run Migrations

```bash
alembic upgrade head
```

### 5. Start the Server

```bash
uvicorn app.main:app --reload
```

The API is now running at **http://localhost:8000**

## API Documentation

| URL                          | Description          |
|------------------------------|----------------------|
| http://localhost:8000/docs   | Swagger UI           |
| http://localhost:8000/redoc  | ReDoc                |
| http://localhost:8000/health | Health check         |

## API Endpoints

### Authentication (`/api/v1/auth`)

| Method | Endpoint    | Description       | Auth Required |
|--------|-------------|-------------------|:---:|
| POST   | /register   | Register new user | No  |
| POST   | /login      | Log in            | No  |
| POST   | /refresh    | Refresh tokens    | No  |
| POST   | /logout     | Log out           | Yes |
| GET    | /me         | Current user      | Yes |

### Users (`/api/v1/users`) — Admin Only

| Method | Endpoint     | Description     |
|--------|-------------|-----------------|
| GET    | /            | List users      |
| GET    | /{id}        | Get user        |
| POST   | /            | Create user     |
| PUT    | /{id}        | Update user     |
| DELETE | /{id}        | Delete user     |

### Doctors (`/api/v1/doctors`)

| Method | Endpoint     | Description       | Access                |
|--------|-------------|-------------------|-----------------------|
| GET    | /            | List doctors      | Authenticated         |
| GET    | /{id}        | Get doctor        | Authenticated         |
| POST   | /            | Create doctor     | Admin only            |
| PUT    | /{id}        | Update doctor     | Admin or own profile  |
| DELETE | /{id}        | Delete doctor     | Admin only            |

### Patients (`/api/v1/patients`)

| Method | Endpoint     | Description       | Access                |
|--------|-------------|-------------------|-----------------------|
| GET    | /            | List patients     | Admin / Doctor        |
| GET    | /{id}        | Get patient       | Admin / Doctor / Own  |
| POST   | /            | Create patient    | Admin only            |
| PUT    | /{id}        | Update patient    | Admin or own profile  |
| DELETE | /{id}        | Delete patient    | Admin only            |

## User Roles

| Role    | Permissions                                               |
|---------|-----------------------------------------------------------|
| Admin   | Full access to all resources                              |
| Doctor  | View all patients, manage own profile, view other doctors |
| Patient | View/edit own profile only                                |

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/test_auth.py -v

# Run specific test class
pytest tests/test_auth.py::TestLogin -v
```

## Environment Variables

| Variable                      | Default                                              | Description              |
|-------------------------------|------------------------------------------------------|--------------------------|
| `APP_NAME`                    | Hospital Appointment API                             | Application name         |
| `APP_VERSION`                 | 1.0.0                                                | Application version      |
| `DEBUG`                       | false                                                | Debug mode               |
| `DATABASE_URL`                | postgresql+asyncpg://postgres:postgres@localhost/...  | Async PostgreSQL URL     |
| `JWT_SECRET_KEY`              | *(change in production)*                             | JWT signing key          |
| `JWT_ALGORITHM`               | HS256                                                | JWT algorithm            |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 30                                                   | Access token TTL         |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | 7                                                    | Refresh token TTL        |
| `CORS_ORIGINS`                | ["http://localhost:3000", "http://localhost:8000"]    | Allowed CORS origins     |

## License

MIT
