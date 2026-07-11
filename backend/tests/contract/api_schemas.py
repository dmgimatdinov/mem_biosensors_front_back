"""
Контракт API — централизованное описание всех схем ответов.
Изменение этих схем требует обновления фронтенда.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any


class BaseResponse(BaseModel):
    """Базовая модель с настройками для PascalCase."""
    model_config = ConfigDict(populate_by_name=True)


# ============ Схемы для сущностей ============

class AnalyteResponse(BaseResponse):
    """Схема ответа для аналита (PascalCase)."""
    TA_ID: str = Field(..., pattern=r"^TA[A-Z0-9_-]{1,30}$")
    TA_Name: str = Field(..., min_length=3, max_length=255)
    PH_Min: float = Field(..., ge=2.0, le=10.0)
    PH_Max: float = Field(..., ge=2.0, le=10.0)
    T_Max: int = Field(..., ge=0, le=180)
    ST: int = Field(..., ge=0, le=365)
    HL: int = Field(..., ge=0, le=8760)
    PC: int = Field(..., ge=0, le=1000)


class BioRecognitionResponse(BaseResponse):
    """Схема ответа для биораспознающего слоя."""
    BRE_ID: str = Field(..., pattern=r"^BRE[A-Z0-9_-]{1,30}$")
    BRE_Name: str = Field(..., min_length=3, max_length=255)
    PH_Min: float = Field(..., ge=2.0, le=10.0)
    PH_Max: float = Field(..., ge=2.0, le=10.0)
    T_Min: int = Field(..., ge=0, le=100)
    T_Max: int = Field(..., ge=0, le=100)
    DR_Min: float = Field(..., ge=0)
    DR_Max: float = Field(..., ge=0)
    SN: int = Field(..., ge=0)
    RP: int = Field(..., ge=0, le=100)
    TR: int = Field(..., ge=0)
    ST: int = Field(..., ge=0, le=365)
    LOD: int = Field(..., ge=0)
    HL: int = Field(..., ge=0, le=8760)
    PC: int = Field(..., ge=0, le=1000)


class ImmobilizationResponse(BaseResponse):
    """Схема ответа для иммобилизационного слоя."""
    IM_ID: str = Field(..., pattern=r"^IM[A-Z0-9_-]{1,30}$")
    IM_Name: str = Field(..., min_length=3, max_length=255)
    PH_Min: float = Field(..., ge=2.0, le=10.0)
    PH_Max: float = Field(..., ge=2.0, le=10.0)
    T_Min: int = Field(..., ge=0, le=100)
    T_Max: int = Field(..., ge=0, le=100)
    MP: int = Field(..., ge=0, le=150)
    Adh: str
    Sol: str
    K_IM: float = Field(..., ge=0, le=1.0)
    RP: int = Field(..., ge=0, le=100)
    TR: int = Field(..., ge=0)
    ST: int = Field(..., ge=0, le=365)
    HL: int = Field(..., ge=0, le=8760)
    PC: int = Field(..., ge=0, le=1000)


class MemristiveResponse(BaseResponse):
    """Схема ответа для мемристивного слоя."""
    MEM_ID: str = Field(..., pattern=r"^MEM[A-Z0-9_-]{1,30}$")
    MEM_Name: str = Field(..., min_length=3, max_length=255)
    PH_Min: float = Field(..., ge=2.0, le=10.0)
    PH_Max: float = Field(..., ge=2.0, le=10.0)
    T_Min: int = Field(..., ge=0, le=100)
    T_Max: int = Field(..., ge=0, le=100)
    DR_Min: float = Field(..., ge=0)
    DR_Max: float = Field(..., ge=0)
    MP: int = Field(..., ge=0, le=150)
    SN: int = Field(..., ge=0)
    RP: int = Field(..., ge=0, le=100)
    TR: int = Field(..., ge=0)
    ST: int = Field(..., ge=0, le=365)
    LOD: int = Field(..., ge=0)
    HL: int = Field(..., ge=0, le=8760)
    PC: int = Field(..., ge=0, le=1000)


class CombinationResponse(BaseResponse):
    """Схема ответа для комбинации."""
    Combo_ID: str = Field(..., pattern=r"^COMBO_")
    TA_ID: str
    BRE_ID: str
    IM_ID: str
    MEM_ID: str
    Score: float = Field(..., ge=0, le=10)
    SN_Total: Optional[float] = None
    TR_Total: Optional[float] = None
    ST_Total: Optional[float] = None
    LOD_Total: Optional[float] = None
    DR_Total: Optional[float] = None
    PC_Total: Optional[float] = None
    Created: Optional[str] = None


# ============ Схемы для служебных ответов ============

class SuccessResponse(BaseResponse):
    """Схема успешного ответа."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseResponse):
    """Схема ошибки."""
    detail: str


class HealthResponse(BaseResponse):
    """Схема ответа /api/health."""
    status: str
    message: str


class StatisticsResponse(BaseResponse):
    """Схема ответа /api/analytics/statistics."""
    pass


class SynthesisResponse(BaseResponse):
    """Схема ответа /api/combinations/synthesize."""
    checked: int = Field(..., ge=0)
    created: int = Field(..., ge=0)
    skipped: Optional[int] = None
    errors: Optional[int] = None
