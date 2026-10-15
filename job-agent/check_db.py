import sqlite3
from db import DB_PATH

connection = sqlite3.connect(DB_PATH)

try:
    cursor = connection.execute(
        """
        SELECT id, question, answer, created_at
        FROM chat_records
        ORDER BY id DESC
        LIMIT 5
        """
    )

    records = cursor.fetchall()

    for record in records:
        print("编号：", record[0])
        print("问题：", record[1])
        print("回答：", record[2])
        print("时间（UTC）：", record[3])
        print("-" * 40)
finally:
    connection.close()