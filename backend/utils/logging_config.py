# utils/logging_config.py

import logging
import sys
from pathlib import Path

def setup_logging(log_file: str = "biosensor.log", level: int = logging.INFO):
    """
    Настройка логирования для приложения.
    
    Args:
        log_file: путь к файлу лога
        level: уровень логирования
    """
    # Создаём директорию для логов, если её нет
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Формат логов
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Настройка корневого логгера
    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            # Вывод в файл
            logging.FileHandler(log_file, encoding='utf-8'),
            # Вывод в консоль
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Снижаем уровень для сторонних библиотек
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Логирование инициализировано: {log_file}")
