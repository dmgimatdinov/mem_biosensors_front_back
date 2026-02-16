# domain/models.py

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class FieldConfig:
    """Конфигурация поля для UI и валидации."""
    # базовые характеристики
    name: Optional[str] = None          # внутреннее имя / ключ
    type: Optional[str] = None          # 'string', 'float', 'int', 'bool', 'range', и т.п.
    constraints: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    required: bool = True
    default: Optional[Any] = None

    # параметры для UI
    label: Optional[str] = None         # отображаемый заголовок ("ID аналита:")
    var_name: Optional[str] = None      # имя переменной в форме Streamlit
    hint: Optional[str] = None          # подсказка/placeholder

    # параметры для диапазонов (range-поля)
    min_var: Optional[str] = None       # имя переменной для минимума
    max_var: Optional[str] = None       # имя переменной для максимума

    def __post_init__(self):
        if self.constraints is None:
            self.constraints = {}
        # если name не задан, подставим var_name (чтобы что-то было)
        if self.name is None and self.var_name is not None:
            self.name = self.var_name

@dataclass
class Analyte:
    ta_id: str
    ta_name: str
    ph_min: Optional[float] = None
    ph_max: Optional[float] = None
    t_max: Optional[float] = None
    stability: Optional[float] = None
    half_life: Optional[float] = None
    power_consumption: Optional[float] = None

@dataclass
class BioRecognitionLayer:
    bre_id: str
    bre_name: str
    ph_min: Optional[float] = None
    ph_max: Optional[float] = None
    t_min: Optional[float] = None
    t_max: Optional[float] = None
    sensitivity: Optional[float] = None
    dr_min: Optional[float] = None
    dr_max: Optional[float] = None
    reproducibility: Optional[float] = None
    response_time: Optional[float] = None
    stability: Optional[float] = None
    lod: Optional[float] = None
    durability: Optional[float] = None
    power_consumption: Optional[float] = None

@dataclass
class ImmobilizationLayer:
    im_id: str
    im_name: str
    ph_min: Optional[float] = None
    ph_max: Optional[float] = None
    t_min: Optional[float] = None
    t_max: Optional[float] = None
    young_modulus: Optional[float] = None
    adhesion: Optional[str] = None
    solubility: Optional[str] = None
    loss_coefficient: Optional[float] = None
    reproducibility: Optional[float] = None
    response_time: Optional[float] = None
    stability: Optional[float] = None
    durability: Optional[float] = None
    power_consumption: Optional[float] = None

@dataclass
class MemristiveLayer:
    mem_id: str
    mem_name: str
    ph_min: Optional[float] = None
    ph_max: Optional[float] = None
    t_min: Optional[float] = None
    t_max: Optional[float] = None
    young_modulus: Optional[float] = None
    sensitivity: Optional[float] = None
    dr_min: Optional[float] = None
    dr_max: Optional[float] = None
    reproducibility: Optional[float] = None
    response_time: Optional[float] = None
    stability: Optional[float] = None
    lod: Optional[float] = None
    durability: Optional[float] = None
    power_consumption: Optional[float] = None

@dataclass
class SensorCombination:
    combo_id: str
    ta_id: str
    bre_id: str
    im_id: str
    mem_id: str
    sn_total: Optional[float] = None
    tr_total: Optional[float] = None
    st_total: Optional[float] = None
    rp_total: Optional[float] = None
    lod_total: Optional[float] = None
    dr_total: Optional[str] = None
    hl_total: Optional[float] = None
    pc_total: Optional[float] = None
    score: Optional[float] = None
    created_at: Optional[str] = None

@dataclass
class Passport:
    """Полный паспорт (четыре слоя + комбинация)"""
    analyte: Analyte
    bio_layer: BioRecognitionLayer
    immobilization_layer: ImmobilizationLayer
    memristive_layer: MemristiveLayer
    combination: Optional[SensorCombination] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация паспорта в словарь"""
        return {
            'analyte': asdict(self.analyte),
            'bio_layer': asdict(self.bio_layer),
            'immobilization_layer': asdict(self.immobilization_layer),
            'memristive_layer': asdict(self.memristive_layer),
            'combination': asdict(self.combination) if self.combination else None,
        }
