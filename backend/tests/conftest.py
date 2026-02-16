# import pytest
# import sqlite3
# from db.manager import DBNAME, DatabaseManager
# from db.exceptions import DatabaseConnectionError

# @pytest.fixture(scope="function")
# def clean_db(tmp_path):  # tmp_path — pytest temp dir
#     temp_db = str(tmp_path / "test.db")
#     db = DatabaseManager(dbname=temp_db)  # Отдельная БД!
#     yield db
#     """Создаёт временную БД, чистит после теста."""
#     # Удалить старую БД
#     # try:
#     #     import os
#     #     if os.path.exists(DBNAME):
#     #         os.remove(DBNAME)
#     # except:
#     #     pass
    
#     # Создать новую
#     # db = DatabaseManager()
#     # yield db
#     # Teardown: удалить тестовые записи или БД
#     try:
#         conn = sqlite3.connect(temp_db)
#         cursor = conn.cursor()
#         cursor.execute("DELETE FROM Analytes WHERE TAID LIKE 'TA_TEST%'")
#         cursor.execute("DELETE FROM BioRecognitionLayers WHERE BREID LIKE 'BRE_TEST%'")
#         cursor.execute("DELETE FROM ImmobilizationLayers WHERE IMID LIKE 'IM_TEST%'")
#         cursor.execute("DELETE FROM MemristiveLayers WHERE MEMID LIKE 'MEM_TEST%'")
#         conn.commit()
#         conn.close()
#     except:
