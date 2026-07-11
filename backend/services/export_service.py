# services/export_service.py

import json
import io
import zipfile
from datetime import datetime
from db.manager import DatabaseManager
from domain.table_config import TABLE_CONFIGS
import pandas as pd

class ExportService:
    """Сервис экспорта данных."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def export_table(self, table_key: str, fmt: str = 'csv') -> tuple[bytes, str]:
        """
        Экспортировать одну таблицу.
        
        Returns:
            (bytes, filename)
        """
        normalized_key = table_key
        alias_map = {
            "Analytes": "analytes",
            "BioRecognitionLayers": "bio_layers",
            "ImmobilizationLayers": "immobilization_layers",
            "MemristiveLayers": "memristive_layers",
            "SensorCombinations": "sensor_combinations",
        }
        if table_key in alias_map:
            normalized_key = alias_map[table_key]

        if normalized_key not in TABLE_CONFIGS:
            raise ValueError(f"Таблица {table_key} не найдена")
        
        config = TABLE_CONFIGS[normalized_key]
        fetch_method = getattr(self.db, config.fetch_method.replace('_paginated', ''))
        data = fetch_method()
        
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        
        if fmt == 'json':
            payload = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
            filename = f"{table_key}_{ts}.json"
            return payload, filename
        if fmt == 'csv':
            df = pd.DataFrame(data)
            payload = df.to_csv(index=False).encode('utf-8-sig')
            filename = f"{table_key}_{ts}.csv"
            return payload, filename
        if fmt == 'excel':
            df = pd.DataFrame(data)
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name=table_key[:31])
            buffer.seek(0)
            payload = buffer.read()
            filename = f"{table_key}_{ts}.xlsx"
            return payload, filename
        raise ValueError(f"Неподдерживаемый формат: {fmt}")
    
    def export_all(self, fmt: str = 'csv') -> tuple[bytes, str]:
        """Экспортировать все таблицы."""
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        
        if fmt == 'json':
            all_data = {}
            for key in TABLE_CONFIGS.keys():
                config = TABLE_CONFIGS[key]
                fetch_method = getattr(self.db, config.fetch_method.replace('_paginated', ''))
                all_data[key] = fetch_method()
            
            payload = json.dumps(all_data, ensure_ascii=False, indent=2).encode('utf-8')
            filename = f"all_data_{ts}.json"
            return payload, filename
        if fmt == 'csv':
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                for key in TABLE_CONFIGS.keys():
                    config = TABLE_CONFIGS[key]
                    fetch_method = getattr(self.db, config.fetch_method.replace('_paginated', ''))
                    data = fetch_method()
                    df = pd.DataFrame(data)
                    zf.writestr(f"{key}.csv", df.to_csv(index=False).encode('utf-8-sig'))
            
            buf.seek(0)
            filename = f"all_data_{ts}.zip"
            return buf.getvalue(), filename
        if fmt == 'excel':
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                for key in TABLE_CONFIGS.keys():
                    config = TABLE_CONFIGS[key]
                    fetch_method = getattr(self.db, config.fetch_method.replace('_paginated', ''))
                    df = pd.DataFrame(fetch_method())
                    sheet_name = key[:31]
                    df.to_excel(writer, index=False, sheet_name=sheet_name)
            buffer.seek(0)
            payload = buffer.read()
            filename = f"all_data_{ts}.xlsx"
            return payload, filename
        raise ValueError(f"Неподдерживаемый формат: {fmt}")
