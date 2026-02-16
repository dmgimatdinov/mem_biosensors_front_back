# db/exceptions.py

class DatabaseError(Exception):
    """Базовая ошибка работы с БД."""
    pass

class DatabaseConnectionError(DatabaseError):
    """Ошибка подключения к БД."""
    pass

class DatabaseIntegrityError(DatabaseError):
    """Ошибка целостности данных."""
    pass

class EntityNotFoundError(DatabaseError):
    """Сущность не найдена."""
    pass
