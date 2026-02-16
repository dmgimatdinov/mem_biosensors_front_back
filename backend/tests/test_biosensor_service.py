# test_biosensor_service.py
from services.biosensor_service import BiosensorService
from db.manager import DatabaseManager

def test_validate_analyte():
    db = DatabaseManager()
    service = BiosensorService(db)
    
    # Валидные данные
    data = {
        "ta_id": "TA001",      # ta_id → taid
        "ta_name": "Glucose",  # ta_name → taname
        "ph_min": 5.0,         # Добавьте обязательные
        "ph_max": 8.0
    }
    result = service.validator.validate("analyte", data) 
    is_valid = result.is_valid
    msg = ", ".join(result.errors) if not is_valid else None
    assert is_valid == True
    
    # Невалидные данные
    data = {"ta_id": "TA001", "ta_name": "Glucose", "t_max": 500.0}  # вне диапазона
    result = service.validator.validate("analyte", data)
    is_valid = result.is_valid
    msg = ", ".join(result.errors) if not is_valid else None
    assert is_valid == False
