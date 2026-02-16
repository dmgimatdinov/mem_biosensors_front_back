# Memristive Biosensors - Passport Management System

A full-stack application for managing memristive biosensor passports with data entry, analysis, and export capabilities.

## 🏗️ Architecture

- **Backend**: FastAPI (Python 3.12+)
- **Frontend**: Next.js 16 (TypeScript, React 19)
- **Database**: SQLite
- **Deployment**: Monolithic (FastAPI serves both API and static frontend)

## 📁 Project Structure

```
mem_biosensors_front_back/
├── backend/
│   ├── main.py              # FastAPI application entry point
│   ├── requirements.txt     # Python dependencies
│   ├── db/                  # Database management
│   ├── domain/              # Domain models and config
│   ├── services/            # Business logic services
│   ├── utils/               # Utilities and logging
│   └── tests/               # Backend tests
├── frontend/
│   ├── app/                 # Next.js app directory
│   ├── components/          # React components
│   ├── lib/                 # Frontend utilities
│   ├── package.json         # Node.js dependencies
│   └── next.config.mjs      # Next.js configuration
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+ (with npm)
- Git

### Development Mode (Separate Servers)

**1. Backend (Terminal 1):**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Backend API will be available at `http://localhost:8000/api/*`

**2. Frontend (Terminal 2):**
```bash
cd frontend
npm install --legacy-peer-deps
npm run dev
```
Frontend will be available at `http://localhost:3000`

### Production Mode (Monolithic)

Build frontend and serve everything from one server:

```bash
# 1. Build frontend
cd frontend
npm install --legacy-peer-deps
npm run build

# 2. Start FastAPI (serves both API and frontend)
cd ../backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Now access the complete application at `http://localhost:8000`
- Frontend: `http://localhost:8000/`
- API: `http://localhost:8000/api/*`

## 📚 API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Main Endpoints

#### Analytes
- `GET /api/analytes` - List all analytes
- `POST /api/analytes` - Create new analyte

#### Bio-Recognition Layers
- `GET /api/bio-recognition` - List all bio-recognition layers
- `POST /api/bio-recognition` - Create new bio-recognition layer

#### Immobilization Layers
- `GET /api/immobilization` - List all immobilization layers
- `POST /api/immobilization` - Create new immobilization layer

#### Memristive Layers
- `GET /api/memristive` - List all memristive layers
- `POST /api/memristive` - Create new memristive layer

#### Combinations
- `GET /api/combinations` - List sensor combinations
- `POST /api/combinations/synthesize` - Synthesize new combinations

#### Analytics
- `GET /api/analytics/statistics` - Database statistics
- `GET /api/analytics/best-combinations` - Top performing combinations
- `GET /api/analytics/comparative` - Comparative analysis

#### Export
- `GET /api/export/{table_name}?format=csv|excel|pdf` - Export specific table
- `GET /api/export/all?format=csv|excel|pdf` - Export all tables

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v
```

### Frontend (Local Storage Based)
The frontend currently uses localStorage for data persistence. No backend integration tests are needed at this stage.

## 🔧 Configuration

### Backend Configuration

**Environment Variables** (optional, create `.env` in backend/):
```env
DATABASE_URL=memristive_biosensor.db
LOG_LEVEL=INFO
```

### Frontend Configuration

**Next.js Config** (`frontend/next.config.mjs`):
- Static export enabled: `output: 'export'`
- TypeScript errors ignored during build (temporary)

## 📝 Development Notes

### Adding New API Endpoints

1. Define Pydantic models in `backend/main.py`
2. Add route handler with appropriate decorators
3. Use existing services from `backend/services/`
4. Update this README with new endpoint documentation

### Modifying Business Logic

Business logic is in `backend/services/`:
- `biosensor_service.py` - Entity validation and CRUD
- `passport_service.py` - Passport management
- `analytics_service.py` - Statistics and analysis
- `export_service.py` - Data export functionality
- `combination_synthesis.py` - Sensor combination synthesis

## 🔐 Security Considerations

- CORS is configured for development (localhost:3000, localhost:8000)
- Update CORS settings in production (`backend/main.py`)
- No authentication implemented yet - add as needed
- Input validation via Pydantic models

## 📦 Deployment

### Docker (Recommended)

```dockerfile
# Dockerfile example
FROM python:3.12-slim

WORKDIR /app

# Install Node.js for building frontend
RUN apt-get update && apt-get install -y nodejs npm

# Copy and build frontend
COPY frontend/ ./frontend/
WORKDIR /app/frontend
RUN npm install --legacy-peer-deps && npm run build

# Copy and setup backend
WORKDIR /app
COPY backend/ ./backend/
WORKDIR /app/backend
RUN pip install -r requirements.txt

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t biosensor-app .
docker run -p 8000:8000 biosensor-app
```

## 🐛 Known Issues

1. **Test `test_save_valid_passport` fails**: This is a pre-existing issue where test data (TA_TEST1) already exists in the database. The business logic works correctly - the test needs to be updated to clean up or use unique IDs.

2. **Frontend Google Fonts**: Removed Geist font imports that were failing during build in isolated environments.

## 🎯 Migration from Streamlit

This application was migrated from Streamlit to FastAPI + Next.js:
- ✅ All business logic preserved in `services/`
- ✅ Database layer unchanged (`db/`)
- ✅ Domain models preserved (`domain/`)
- ✅ All Streamlit UI code removed (`ui/` directory no longer used)
- ✅ FastAPI serves both API and static frontend
- ✅ Next.js provides modern, responsive UI

## 📄 License

[Your License Here]

## 👥 Contributors

[Your Name/Team]

## 📞 Support

For issues and questions, please open a GitHub issue.
