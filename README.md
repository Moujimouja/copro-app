# Copro App

A modern monorepo application with FastAPI backend, React frontend, and PostgreSQL database.

## 🏗️ Architecture

This project follows a monorepo structure with separate backend and frontend services:

```
copro-app/
 ├─ backend/          # FastAPI backend application
 ├─ frontend/         # React frontend application
 ├─ docker-compose.yml
 └─ docs/             # Project documentation
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Running with Docker Compose

1. Clone the repository and navigate to the project directory:
   ```bash
   cd copro-app
   ```

2. Start all services:
   ```bash
   docker-compose up --build
   ```

3. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - PostgreSQL: localhost:5432

### Running Services Locally

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

**Note:** Make sure PostgreSQL is running (via Docker Compose or locally) before starting the backend.

## 📁 Project Structure

### Backend

- `app/main.py` - FastAPI application entry point
- `app/api/` - API route handlers
- `app/core/` - Core configuration and settings
- `app/models/` - SQLAlchemy database models
- `app/db.py` - Database connection and session management
- `app/auth.py` - Authentication and authorization utilities

### Frontend

- `src/App.jsx` - Main React application component
- `src/main.jsx` - React entry point
- `package.json` - Node.js dependencies and scripts

## 🔐 Authentication

The application includes JWT-based authentication:

- **Register**: `POST /api/v1/auth/register`
- **Login**: `POST /api/v1/auth/login`
- **Get Current User**: `GET /api/v1/auth/me` (requires authentication)

## 🛠️ Development

### Environment Variables

Create a `.env` file in the `backend/` directory for local development:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/coproapp
SECRET_KEY=your-secret-key-here
```

### Database Migrations

The application uses SQLAlchemy with automatic table creation. For production, consider using Alembic for migrations.

### API Documentation

FastAPI automatically generates interactive API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📚 Documentation

- [Architecture](./docs/ARCHITECTURE.md) - System architecture overview
- [Decisions](./docs/DECISIONS.md) - Architecture decision records
- [Roadmap](./docs/ROADMAP.md) - Project roadmap and future plans

## 🧪 Testing

```bash
# Backend tests (to be implemented)
cd backend
pytest

# Frontend tests (to be implemented)
cd frontend
npm test
```

## 📝 License

[Add your license here]


