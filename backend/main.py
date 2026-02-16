# main.py - FastAPI Backend for Memristive Biosensors
from fastapi import FastAPI, HTTPException, status, Path as PathParam, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional, Tuple
import logging
import os
from pathlib import Path
from io import BytesIO

# Import business logic services
from db.manager import DatabaseManager
from db.exceptions import DatabaseConnectionError, DatabaseIntegrityError
from services.biosensor_service import BiosensorService
from services.passport_service import PassportService
from services.analytics_service import AnalyticsService
from services.export_service import ExportService
from services.combination_synthesis import CombinationSynthesisService
from domain.models import Analyte, BioRecognitionLayer, ImmobilizationLayer, MemristiveLayer
from utils.logging_config import setup_logging

# Setup logging
setup_logging(log_file="logs/biosensor.log", level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Memristive Biosensors API",
    description="API for managing memristive biosensor passports",
    version="2.0.0"
)

# CORS middleware for React development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database and services
db_manager = None
biosensor_service = None
passport_service = None
analytics_service = None
export_service = None
combination_service = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global db_manager, biosensor_service, passport_service, analytics_service, export_service, combination_service
    try:
        db_manager = DatabaseManager()
        biosensor_service = BiosensorService(db_manager)
        passport_service = PassportService(db_manager)
        analytics_service = AnalyticsService(db_manager)
        export_service = ExportService(db_manager)
        combination_service = CombinationSynthesisService(db_manager)
        logger.info("✅ All services initialized successfully")
    except DatabaseConnectionError as e:
        logger.error(f"❌ Failed to connect to database: {e}")
        raise


# ==================== Pydantic Models for API ====================

class AnalyteCreate(BaseModel):
    ta_id: str = Field(..., pattern=r'^TA[A-Z0-9_-]{1,20}$')
    ta_name: str = Field(..., min_length=3, max_length=255)
    ph_min: float = Field(..., ge=2.0, le=10.0)
    ph_max: float = Field(..., ge=2.0, le=10.0)
    t_max: int = Field(..., ge=0, le=180)
    stability: int = Field(..., ge=0, le=365)
    half_life: int = Field(..., ge=0, le=8760)
    power_consumption: int = Field(..., ge=0, le=1000)


class BioRecognitionCreate(BaseModel):
    bre_id: str = Field(..., pattern=r'^BRE[A-Z0-9_-]{1,20}$')
    bre_name: str = Field(..., min_length=3, max_length=255)
    ph_min: float = Field(..., ge=2.0, le=10.0)
    ph_max: float = Field(..., ge=2.0, le=10.0)
    t_min: int = Field(..., ge=4, le=120)
    t_max: int = Field(..., ge=4, le=120)
    dr_min: float = Field(..., ge=0.1, le=1000000000000.0)
    dr_max: float = Field(..., ge=0.1, le=1000000000000.0)
    sensitivity: int = Field(..., ge=0, le=20000)
    reproducibility: int = Field(..., ge=0, le=100)
    response_time: int = Field(..., ge=0, le=3600)
    stability: int = Field(..., ge=0, le=365)
    lod: int = Field(..., ge=0, le=50000)
    durability: int = Field(..., ge=0, le=8760)
    power_consumption: int = Field(..., ge=0, le=1000)


class ImmobilizationCreate(BaseModel):
    im_id: str = Field(..., pattern=r'^IM[A-Z0-9_-]{1,20}$')
    im_name: str = Field(..., min_length=3, max_length=255)
    ph_min: float = Field(..., ge=2.0, le=10.0)
    ph_max: float = Field(..., ge=2.0, le=10.0)
    t_min: int = Field(..., ge=4, le=120)
    t_max: int = Field(..., ge=4, le=120)
    young_modulus: int = Field(..., ge=0, le=1000)
    adhesion: str = Field(..., pattern=r'^(слабая|хорошая|отличная)$')
    solubility: str = Field(..., pattern=r'^(водорастворимый|органический|нерастворимый)$')
    loss_coefficient: float = Field(..., ge=0.0, le=1.0)
    reproducibility: int = Field(..., ge=0, le=100)
    response_time: int = Field(..., ge=0, le=3600)
    stability: int = Field(..., ge=0, le=365)
    durability: int = Field(..., ge=0, le=8760)
    power_consumption: int = Field(..., ge=0, le=1000)


class MemristiveCreate(BaseModel):
    mem_id: str = Field(..., pattern=r'^MEM[A-Z0-9_-]{1,20}$')
    mem_name: str = Field(..., min_length=3, max_length=255)
    ph_min: float = Field(..., ge=2.0, le=10.0)
    ph_max: float = Field(..., ge=2.0, le=10.0)
    t_min: int = Field(..., ge=5, le=120)
    t_max: int = Field(..., ge=5, le=120)
    dr_min: float = Field(..., ge=0.0000001, le=100000000000.0)
    dr_max: float = Field(..., ge=0.0000001, le=100000000000.0)
    young_modulus: int = Field(..., ge=0, le=1000)
    sensitivity: int = Field(..., ge=0, le=20000)
    reproducibility: int = Field(..., ge=0, le=100)
    response_time: int = Field(..., ge=0, le=3600)
    stability: int = Field(..., ge=0, le=365)
    lod: int = Field(..., ge=0, le=50000)
    durability: int = Field(..., ge=0, le=8760)
    power_consumption: int = Field(..., ge=0, le=1000)


class PassportSave(BaseModel):
    analyte: AnalyteCreate
    bio_recognition: BioRecognitionCreate
    immobilization: ImmobilizationCreate
    memristive: MemristiveCreate


class SuccessResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None


# ==================== API Endpoints ====================

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "API is running"}


# ==================== Analytes Endpoints ====================

@app.get("/api/analytes", response_model=List[Dict[str, Any]])
async def get_analytes(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get all analytes"""
    try:
        analytes = biosensor_service.get_all_entities("analyte", limit=limit, offset=offset)
        return analytes
    except Exception as e:
        logger.error(f"Error fetching analytes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analytes", response_model=SuccessResponse)
async def create_analyte(analyte: AnalyteCreate):
    """Create a new analyte"""
    try:
        data = analyte.dict()
        success, message = biosensor_service.save_entity("analyte", data)
        if success:
            return SuccessResponse(success=True, message=message)
        else:
            raise HTTPException(status_code=400, detail=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating analyte: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Bio Recognition Endpoints ====================

@app.get("/api/bio-recognition", response_model=List[Dict[str, Any]])
async def get_bio_recognition(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get all bio recognition layers"""
    try:
        layers = biosensor_service.get_all_entities("bio_recognition", limit=limit, offset=offset)
        return layers
    except Exception as e:
        logger.error(f"Error fetching bio recognition layers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/bio-recognition", response_model=SuccessResponse)
async def create_bio_recognition(layer: BioRecognitionCreate):
    """Create a new bio recognition layer"""
    try:
        data = layer.dict()
        success, message = biosensor_service.save_entity("bio_recognition", data)
        if success:
            return SuccessResponse(success=True, message=message)
        else:
            raise HTTPException(status_code=400, detail=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating bio recognition layer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Immobilization Endpoints ====================

@app.get("/api/immobilization", response_model=List[Dict[str, Any]])
async def get_immobilization(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get all immobilization layers"""
    try:
        layers = biosensor_service.get_all_entities("immobilization", limit=limit, offset=offset)
        return layers
    except Exception as e:
        logger.error(f"Error fetching immobilization layers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/immobilization", response_model=SuccessResponse)
async def create_immobilization(layer: ImmobilizationCreate):
    """Create a new immobilization layer"""
    try:
        data = layer.dict()
        success, message = biosensor_service.save_entity("immobilization", data)
        if success:
            return SuccessResponse(success=True, message=message)
        else:
            raise HTTPException(status_code=400, detail=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating immobilization layer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Memristive Endpoints ====================

@app.get("/api/memristive", response_model=List[Dict[str, Any]])
async def get_memristive(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get all memristive layers"""
    try:
        layers = biosensor_service.get_all_entities("memristive", limit=limit, offset=offset)
        return layers
    except Exception as e:
        logger.error(f"Error fetching memristive layers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/memristive", response_model=SuccessResponse)
async def create_memristive(layer: MemristiveCreate):
    """Create a new memristive layer"""
    try:
        data = layer.dict()
        success, message = biosensor_service.save_entity("memristive", data)
        if success:
            return SuccessResponse(success=True, message=message)
        else:
            raise HTTPException(status_code=400, detail=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating memristive layer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Combinations Endpoints ====================

@app.get("/api/combinations")
async def get_combinations(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get all sensor combinations"""
    try:
        combinations = db_manager.list_all_sensor_combinations_paginated(limit=limit, offset=offset)
        return combinations
    except Exception as e:
        logger.error(f"Error fetching combinations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/combinations/synthesize")
async def synthesize_combinations(max_combinations: int = Query(10000, ge=1, le=50000)):
    """Synthesize new sensor combinations"""
    try:
        checked, created = combination_service.synthesize_all_combinations(max_combinations=max_combinations)
        return {
            "success": True,
            "checked": checked,
            "created": created,
            "message": f"✅ Checked {checked} possible combinations, created {created} new ones"
        }
    except Exception as e:
        logger.error(f"Error synthesizing combinations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Analytics Endpoints ====================

@app.get("/api/analytics/statistics")
async def get_statistics():
    """Get database statistics"""
    try:
        stats = analytics_service.get_database_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/best-combinations")
async def get_best_combinations(limit: int = Query(10, ge=1, le=100)):
    """Get best sensor combinations"""
    try:
        combinations = analytics_service.get_best_combinations(limit=limit)
        return combinations
    except Exception as e:
        logger.error(f"Error fetching best combinations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/comparative")
async def get_comparative_analysis():
    """Get comparative analysis of layers"""
    try:
        analysis = analytics_service.get_comparative_analysis()
        return analysis
    except Exception as e:
        logger.error(f"Error fetching comparative analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Export Endpoints ====================

@app.get("/api/export/{table_name}")
async def export_table(
    table_name: str = PathParam(...),
    format: str = Query("csv", pattern=r'^(csv|excel|pdf)$')
):
    """Export a specific table"""
    try:
        content, filename = export_service.export_table(table_name, fmt=format)
        
        media_types = {
            "csv": "text/csv",
            "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "pdf": "application/pdf"
        }
        
        return StreamingResponse(
            BytesIO(content),
            media_type=media_types.get(format, "application/octet-stream"),
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Error exporting table: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/all")
async def export_all(format: str = Query("csv", pattern=r'^(csv|excel|pdf)$')):
    """Export all tables"""
    try:
        content, filename = export_service.export_all(fmt=format)
        
        media_types = {
            "csv": "application/zip",
            "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "pdf": "application/pdf"
        }
        
        return StreamingResponse(
            BytesIO(content),
            media_type=media_types.get(format, "application/octet-stream"),
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Error exporting all tables: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Static Files & SPA Routing ====================

# Check if React build directory exists
frontend_build_path = Path(__file__).parent.parent / "frontend" / "build"
if frontend_build_path.exists():
    # Mount static files
    app.mount("/static", StaticFiles(directory=str(frontend_build_path / "static")), name="static")
    
    # Serve index.html for root and SPA routes
    @app.get("/{full_path:path}")
    async def serve_react(full_path: str):
        """Serve React app for all non-API routes"""
        # Don't intercept API routes
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        
        index_file = frontend_build_path / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        else:
            raise HTTPException(status_code=404, detail="React app not built yet")
else:
    logger.warning(f"⚠️  Frontend build directory not found at {frontend_build_path}")
    logger.warning("⚠️  React app will not be served. Build the frontend first.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
