"""
Контракт API — централизованное описание всех схем ответов.
Изменение этих схем требует обновления фронтенда.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any


class BaseResponse(BaseModel):
    """Базовая модель с настройками для PascalCase."""
    # extra="forbid" гарантирует падение тестов при появлении неожиданных полей в API.
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


# ============ Схемы для сущностей ============

class AnalyteResponse(BaseResponse):
    """Схема ответа для аналита (PascalCase)."""
    TA_ID: str = Field(..., pattern=r"^TA[A-Z0-9_-]{1,30}$")
    TA_Name: str = Field(..., min_length=3, max_length=255)
    PH_Min: float = Field(..., ge=2.0, le=10.0)
    PH_Max: float = Field(..., ge=2.0, le=10.0)
    T_Max: int = Field(..., ge=0, le=180)
    ST: int = Field(..., ge=0, le=365)


class BioRecognitionResponse(BaseResponse):
    """Схема ответа для биораспознающего слоя."""
    BRE_ID: str = Field(..., pattern=r"^BRE[A-Z0-9_-]{1,30}$")
    BRE_Name: str = Field(..., min_length=3, max_length=255)
    PH_Min: float = Field(..., ge=2.0, le=10.0)
    PH_Max: float = Field(..., ge=2.0, le=10.0)
    T_Min: int = Field(..., ge=0, le=100)
    T_Max: int = Field(..., ge=0, le=100)
    SN: int = Field(..., ge=0)


class ImmobilizationResponse(BaseResponse):
    """Схема ответа для иммобилизационного слоя."""
    IM_ID: str = Field(..., pattern=r"^IM[A-Z0-9_-]{1,30}$")
    IM_Name: str = Field(..., min_length=3, max_length=255)
    PH_Min: float = Field(..., ge=2.0, le=10.0)
    PH_Max: float = Field(..., ge=2.0, le=10.0)
    T_Min: int = Field(..., ge=0, le=100)
    T_Max: int = Field(..., ge=0, le=100)
    MP: int = Field(..., ge=0, le=150)


class MemristiveResponse(BaseResponse):
    """Схема ответа для мемристивного слоя."""
    MEM_ID: str = Field(..., pattern=r"^MEM[A-Z0-9_-]{1,30}$")
    MEM_Name: str = Field(..., min_length=3, max_length=255)
    PH_Min: float = Field(..., ge=2.0, le=10.0)
    PH_Max: float = Field(..., ge=2.0, le=10.0)
    T_Min: int = Field(..., ge=0, le=100)
    T_Max: int = Field(..., ge=0, le=100)
    SN: int = Field(..., ge=0)


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


class StatisticsItem(BaseResponse):
    """Элемент статистики по отдельной таблице."""
    label: str
    count: int = Field(..., ge=0)
    error: Optional[str] = None


class StatisticsResponse(BaseResponse):
    """Схема ответа /api/analytics/statistics."""
    Analytes: StatisticsItem
    BioRecognitionLayers: StatisticsItem
    ImmobilizationLayers: StatisticsItem
    MemristiveLayers: StatisticsItem
    SensorCombinations: StatisticsItem


class SynthesisResponse(BaseResponse):
    """Схема ответа /api/combinations/synthesize."""
    success: bool
    checked: int = Field(..., ge=0)
    created: int = Field(..., ge=0)
    message: str
    skipped: Optional[int] = None
    errors: Optional[int] = None
