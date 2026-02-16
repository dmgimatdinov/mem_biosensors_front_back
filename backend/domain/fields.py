# domain/fields.py

from dataclasses import dataclass
from typing import Literal, Optional, Any, Dict

FieldType = Literal["text", "number", "select", "range"]

@dataclass
class UIField:
    name: str
    label: str
    type: FieldType
    min_value: Optional[float | int] = None
    max_value: Optional[float | int] = None
    help: str = ""
    options: Optional[list[str]] = None          # для select
    group: Optional[str] = None                  # аналит / bio / immob / mem
    column: Optional[int] = None                 # 1 или 2 — левая/правая колонка

# Группа «анализ» (левая колонка)
ANALYTE_FIELDS: list[UIField] = [
    UIField("ta_id", "ID аналита", "text", help="Например: TA001", group="analyte", column=1),
    UIField("ta_name", "Название", "text", help="Полное название аналита", group="analyte", column=1),
    UIField("ph_min", "pH минимум", "number", 2.0, 10.0, "2.0 — 10.0", group="analyte", column=1),
    UIField("ph_max", "pH максимум", "number", 2.0, 10.0, "2.0 — 10.0", group="analyte", column=1),
    UIField("t_max", "Макс. температура (°C)", "number", 0, 180, "0-180", group="analyte", column=1),
    UIField("stability", "Стабильность (дни)", "number", 0, 365, "0-365", group="analyte", column=1),
    UIField("half_life", "Период полураспада (ч)", "number", 0, 8760, "0-8760", group="analyte", column=1),
    UIField("power_consumption", "Энергопотребление (мВт)", "number", 0, 1000, "0-1000", group="analyte", column=1),
]

BIO_FIELDS: list[UIField] = [
    UIField("bre_id", "ID биослоя", "text", help="Например: BRE001", group="bio", column=1),
    UIField("bre_name", "Название", "text", help="Тип биослоя", group="bio", column=1),
    UIField("ph_min", "pH минимум", "number", 2.0, 10.0, "2.0 — 10.0", group="bio", column=1),
    UIField("ph_max", "pH максимум", "number", 2.0, 10.0, "2.0 — 10.0", group="bio", column=1),
    UIField("t_min", "Температура минимум (°C)", "number", 4, 120, "4 — 120", group="bio", column=1),
    UIField("t_max", "Температура максимум (°C)", "number", 4, 120, "4 — 120", group="bio", column=1),
    UIField("dr_min", "Диапазон минимум (пМ)", "number", 0.1, 1e12, "0.1 — 1*10^12", group="bio", column=1),
    UIField("dr_max", "Диапазон максимум (пМ)", "number", 0.1, 1e12, "0.1 — 1*10^12", group="bio", column=1),
    UIField("sensitivity", "Чувствительность (мкА/(мкМ*см²))", "number", 0.0, 20000.0, "0.01 — 1000", group="bio", column=1),
    UIField("reproducibility", "Воспроизводимость (%)", "number", 0, 100, "0-100", group="bio", column=1),
    UIField("response_time", "Время отклика (с)", "number", 0, 3600, "0-3600", group="bio", column=1),
    UIField("stability", "Стабильность (дни)", "number", 0, 365, "0-365", group="bio", column=1),
    UIField("lod", "Предел обнаружения (нМ)", "number", 0, 100000, "0-100000", group="bio", column=1),
    UIField("durability", "Долговечность (ч)", "number", 0, 100000, "0-100000", group="bio", column=1),
    UIField("power_consumption", "Энергопотребление (мВт)", "number", 0, 1000, "0-1000", group="bio", column=1),
]

IMMOB_FIELDS: list[UIField] = [
    UIField("im_id", "ID иммобилизации", "text", help="Например: IM001", group="immob", column=2),
    UIField("im_name", "Название", "text", help="Тип иммобилизации", group="immob", column=2),
    UIField("ph_min", "pH минимум", "number", 2.0, 10.0, "2.0 — 10.0", group="immob", column=2),
    UIField("ph_max", "pH максимум", "number", 2.0, 10.0, "2.0 — 10.0", group="immob", column=2),
    UIField("t_min", "Температура минимум (°C)", "number", 4, 120, "4 — 95", group="immob", column=2),
    UIField("t_max", "Температура максимум (°C)", "number", 4, 120, "4 — 95", group="immob", column=2),
    UIField("young_modulus", "Модуль Юнга (ГПа)", "number", 0, 1000, "0-1000", group="immob", column=2),
    UIField("adhesion", "Адгезия", "select", options=["низкая", "средняя", "высокая"], help="Уровень адгезии", group="immob", column=2),
    UIField("solubility", "Растворимость", "select", options=["низкая", "средняя", "высокая"], help="Уровень растворимости", group="immob", column=2),
    UIField("loss_coefficient", "Коэффициент потерь", "number", 0.0, 1.0, "0-1", group="immob", column=2),
    UIField("reproducibility", "Воспроизводимость (%)", "number", 0, 100, "0-100", group="immob", column=2),
    UIField("response_time", "Время отклика (с)", "number", 0, 3600, "0-3600", group="immob", column=2),
    UIField("stability", "Стабильность (дни)", "number", 0, 365, "0-365", group="immob", column=2),
    UIField("durability", "Долговечность (ч)", "number", 0, 8760, "0-8760", group="immob", column=2),
    UIField("power_consumption", "Энергопотребление (мВт)", "number", 0, 1000, "0-1000", group="immob", column=2),
]

MEM_FIELDS: list[UIField] = [
    UIField("mem_id", "ID мемристора", "text", help="Например: MEM001", group="mem", column=2),
    UIField("mem_name", "Название", "text", help="Тип мемристора", group="mem", column=2),
    UIField("ph_min", "pH минимум", "number", 2.0, 10.0, "2.0 — 10.0", group="mem", column=2),
    UIField("ph_max", "pH максимум", "number", 2.0, 10.0, "2.0 — 10.0", group="mem", column=2),
    UIField("t_min", "Температура минимум (°C)", "number", 5, 120, "5 — 100", group="mem", column=2),
    UIField("t_max", "Температура максимум (°C)", "number", 5, 120, "5 — 100", group="mem", column=2),
    UIField("dr_min", "Диапазон минимум (пМ)", "number", 1e-7, 1e11, "0.0000001 — 1*10^11", group="mem", column=2),
    UIField("dr_max", "Диапазон максимум (пМ)", "number", 1e-7, 1e11, "0.0000001 — 1*10^11", group="mem", column=2),
    UIField("young_modulus", "Модуль Юнга (ГПа)", "number", 0, 1000, "0-1000", group="mem", column=2),
    UIField("sensitivity", "Чувствительность (мВ/dec)", "number", 0.0, 1000.0, "0-1000", group="mem", column=2),
    UIField("reproducibility", "Воспроизводимость (%)", "number", 0, 100, "0-100", group="mem", column=2),
    UIField("response_time", "Время отклика (с)", "number", 0, 3600, "0-3600", group="mem", column=2),
    UIField("stability", "Стабильность (дни)", "number", 0, 365, "0-365", group="mem", column=2),
    UIField("lod", "Предел обнаружения (нМ)", "number", 0, 100000, "0-1*10^5", group="mem", column=2),
    UIField("durability", "Долговечность (ч)", "number", 0, 100000, "0-8760", group="mem", column=2),
    UIField("power_consumption", "Энергопотребление (мВт)", "number", 0, 1000, "0-1000", group="mem", column=2),
]

ALL_FIELDS: list[UIField] = ANALYTE_FIELDS + BIO_FIELDS + IMMOB_FIELDS + MEM_FIELDS
