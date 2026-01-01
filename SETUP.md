# Docker Setup Guide

## Quick Start

1. **Create .env file** (copy from .env.example if needed):
   ```bash
   cp .env.example .env
   ```

2. **Build and start all services**:
   ```bash
   docker compose down -v  # Remove volumes and reset DB
   docker compose up --build
   ```

3. **Access the services**:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Database Admin (Adminer): http://localhost:8080
   - PostgreSQL: localhost:5432

## Services

- **backend**: FastAPI application on port 8000
- **frontend**: React + Vite dev server on port 5173
- **db**: PostgreSQL 15 database
- **adminer**: Database administration tool on port 8080

## Database Connection

- Host: `db` (from within Docker) or `localhost` (from host)
- Port: `5432`
- User: `copro`
- Password: `copro_password`
- Database: `copro_app`

## Troubleshooting

If services don't start:
1. Check logs: `docker compose logs [service-name]`
2. Verify .env file exists and has correct values
3. Ensure ports 5173, 8000, 5432, 8080 are not in use
4. Try: `docker compose down -v && docker compose up --build --force-recreate`
