# Architecture Documentation

## Overview

Copro App is a full-stack web application built with a microservices-oriented architecture, containerized with Docker, and orchestrated with Docker Compose.

## System Architecture

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │
       │ HTTP/HTTPS
       │
┌──────▼─────────────────────────────────────┐
│         Docker Compose Network             │
│                                            │
│  ┌──────────────┐      ┌──────────────┐   │
│  │   Frontend   │◄────►│   Backend    │   │
│  │   (React)    │      │   (FastAPI)  │   │
│  │   :3000      │      │   :8000      │   │
│  └──────────────┘      └──────┬───────┘   │
│                               │           │
│                               │ SQL       │
│                               │           │
│                      ┌────────▼───────┐   │
│                      │   PostgreSQL   │   │
│                      │   :5432        │   │
│                      └────────────────┘   │
└────────────────────────────────────────────┘
```

## Components

### Frontend (React)

- **Technology**: React 18 with Vite
- **Port**: 3000
- **Purpose**: User interface and client-side logic
- **Communication**: RESTful API calls to backend

**Key Features**:
- React Router for navigation
- Axios for HTTP requests
- Modern ES6+ JavaScript
- Hot module replacement for development

### Backend (FastAPI)

- **Technology**: FastAPI (Python 3.11)
- **Port**: 8000
- **Purpose**: API server, business logic, authentication
- **Database**: PostgreSQL via SQLAlchemy ORM

**Key Features**:
- RESTful API design
- JWT-based authentication
- SQLAlchemy ORM for database operations
- Automatic OpenAPI/Swagger documentation
- CORS middleware for frontend communication

### Database (PostgreSQL)

- **Technology**: PostgreSQL 15
- **Port**: 5432
- **Purpose**: Persistent data storage
- **ORM**: SQLAlchemy

**Key Features**:
- ACID compliance
- Relational data model
- Connection pooling
- Health checks for service dependencies

## Data Flow

1. **User Request**: Browser sends HTTP request to frontend
2. **Frontend Processing**: React handles routing and UI updates
3. **API Call**: Frontend makes HTTP request to backend API
4. **Backend Processing**: FastAPI handles request, validates, authenticates
5. **Database Query**: SQLAlchemy executes SQL queries
6. **Response**: Data flows back through the stack to the browser

## Authentication Flow

1. User submits credentials via login form
2. Frontend sends credentials to `/api/v1/auth/login`
3. Backend validates credentials against database
4. Backend generates JWT token
5. Frontend stores token in localStorage
6. Subsequent requests include token in Authorization header
7. Backend validates token and extracts user information

## Security Considerations

- **Password Hashing**: bcrypt for password storage
- **JWT Tokens**: Secure token-based authentication
- **CORS**: Configured for specific origins
- **Environment Variables**: Sensitive data stored in environment variables
- **SQL Injection**: Protected by SQLAlchemy ORM

## Scalability

### Current Architecture
- Single instance of each service
- Suitable for small to medium applications

### Future Considerations
- Load balancing for multiple backend instances
- Database replication for read scalability
- Caching layer (Redis) for frequently accessed data
- CDN for static frontend assets
- Message queue for asynchronous processing

## Deployment

### Development
- Docker Compose for local development
- Hot reload for both frontend and backend
- Volume mounts for live code updates

### Production (Future)
- Container orchestration (Kubernetes, Docker Swarm)
- Reverse proxy (Nginx, Traefik)
- SSL/TLS certificates
- Database backups
- Monitoring and logging (Prometheus, Grafana, ELK)

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Frontend Framework | React | 18.2.0 |
| Build Tool | Vite | 5.0.0 |
| Backend Framework | FastAPI | 0.104.1 |
| Python Runtime | Python | 3.11 |
| Database | PostgreSQL | 15 |
| ORM | SQLAlchemy | 2.0.23 |
| Authentication | JWT (python-jose) | 3.3.0 |
| Containerization | Docker | Latest |
| Orchestration | Docker Compose | 3.8 |

## Dependencies

### Backend Dependencies
- FastAPI: Web framework
- Uvicorn: ASGI server
- SQLAlchemy: ORM
- psycopg2: PostgreSQL adapter
- python-jose: JWT handling
- passlib: Password hashing
- pydantic: Data validation

### Frontend Dependencies
- React: UI framework
- React Router: Client-side routing
- Axios: HTTP client
- Vite: Build tool and dev server



