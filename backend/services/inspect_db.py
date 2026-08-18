# inspect_db.py
import sqlite3
import sys

db_path = sys.argv[1] if len(sys.argv) > 1 else 'memristive_biosensor.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Список таблиц
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]
print(f"📋 Таблицы в {db_path}:")
for t in tables:
    print(f"  - {t}")

# Содержимое каждой таблицы
for table in tables:
    print(f"\n{'='*50}")
    print(f"📊 Таблица: {table}")
    print('='*50)
    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()
    
    # Заголовки
    columns = [desc[0] for desc in cursor.description]
    print(" | ".join(columns))
    print("-" * 50)
    
    # Данные
    for row in rows:
        print(" | ".join(str(v) for v in row))
    
    print(f"Всего записей: {len(rows)}")

conn.close()