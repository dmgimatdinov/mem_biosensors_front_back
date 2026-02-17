# Frontend-Backend Integration

## Overview

This project has been updated to integrate the Next.js frontend with the FastAPI backend. The frontend now fetches data from the backend API instead of using localStorage.

## Architecture

### Backend (FastAPI)
- **Location**: `/backend`
- **Port**: 8000
- **API Endpoints**:
  - `/api/health` - Health check
  - `/api/analytes` - Analyte CRUD operations
  - `/api/bio-recognition` - Bio-recognition layer CRUD
  - `/api/immobilization` - Immobilization layer CRUD
  - `/api/memristive` - Memristive layer CRUD
  - `/api/combinations` - Sensor combinations
  - `/api/combinations/synthesize` - Generate new combinations
  - `/api/analytics/*` - Analytics endpoints
  - `/api/export/*` - Export endpoints

### Frontend (Next.js 16)
- **Location**: `/frontend`
- **Port**: 3000
- **Features**:
  - Data Entry: Create biosensor passports
  - Database: View all stored data
  - Analysis: Synthesize and analyze sensor combinations
  - Export: Download data in various formats

## Setup Instructions

### 1. Backend Setup

```bash
cd backend
pip install -r requirements.txt
python main.py
```

The backend will start on `http://localhost:8000`

### 2. Frontend Setup

```bash
cd frontend
npm install --legacy-peer-deps
cp .env.example .env.local  # Optional: configure API URL
npm run dev
```

The frontend will start on `http://localhost:3000`

### 3. Environment Configuration

Create a `.env.local` file in the frontend directory (optional):

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Integration Details

### API Service Layer

The integration uses a clean layered architecture:

1. **API Configuration** (`lib/api-config.ts`)
   - Centralizes API endpoints and configuration
   - Supports environment-based URL configuration

2. **API Service** (`lib/api-service.ts`)
   - Typed HTTP request functions
   - Field name mapping between frontend (snake_case) and backend (PascalCase)
   - Error handling

3. **Custom Hooks** (`hooks/use-biosensor-data.ts`)
   - React hooks for data fetching and mutations
   - Loading and error states
   - Automatic data refetching after mutations

### Field Mapping

The frontend uses `snake_case` field names (e.g., `ta_id`, `ph_min`) while the backend uses `PascalCase` format (e.g., `TA_ID`, `PH_Min`). The API service layer automatically handles the conversion.

### Features

- ✅ Real-time data fetching from backend
- ✅ CRUD operations for all entity types
- ✅ Combination synthesis via backend API
- ✅ Error handling with user-friendly notifications
- ✅ Loading states during API calls
- ✅ TypeScript type safety across API boundaries
- ✅ CORS configured for development

## Testing

1. Start both backend and frontend servers
2. Navigate to `http://localhost:3000`
3. Test the following flows:
   - Data Entry: Create new biosensor components
   - Database: View paginated data from backend
   - Analysis: Run synthesis to generate combinations
   - Export: Download data (uses backend API)

## Troubleshooting

### Connection Errors

If you see "Connection Error" on the frontend:
1. Ensure backend is running on port 8000
2. Check CORS configuration in `backend/main.py`
3. Verify `NEXT_PUBLIC_API_URL` in `.env.local`

### 422 Validation Errors

The backend validates all input data. Ensure:
- IDs match the required patterns (e.g., `TA001` for analytes)
- All required fields are filled
- Values are within acceptable ranges

## Development

### Adding New Endpoints

1. Add endpoint URL to `frontend/lib/api-config.ts`
2. Create typed service function in `frontend/lib/api-service.ts`
3. Add field mapping if needed
4. Create custom hook in `frontend/hooks/use-biosensor-data.ts` (optional)
5. Use in components

### Code Structure

```
frontend/
├── app/                    # Next.js App Router pages
├── components/             # React components
├── hooks/                  # Custom React hooks
│   └── use-biosensor-data.ts  # Data fetching hooks
├── lib/                    # Utilities and services
│   ├── api-config.ts      # API configuration
│   ├── api-service.ts     # HTTP service layer
│   └── biosensor-store.ts # Type definitions
└── .env.example           # Environment template
```

## Production Deployment

For production:

1. Build the frontend:
   ```bash
   cd frontend
   npm run build
   ```

2. Set production environment variables:
   ```env
   NEXT_PUBLIC_API_URL=https://your-api-domain.com
   ```

3. The backend can serve the built frontend from the `frontend/out` directory

## License

[Add your license information here]
