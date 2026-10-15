import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("job_agent.db")


def init_db():
    connection = sqlite3.connect(DB_PATH)

    try:
        # 新数据库：直接创建包含 session_id 的表
        connection.execute("""
            CREATE TABLE IF NOT EXISTS chat_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL DEFAULT 'default',
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 旧数据库：检查是否缺少 session_id 字段
        columns = connection.execute(
            "PRAGMA table_info(chat_records)"
        ).fetchall()

        column_names = [column[1] for column in columns]

        if "session_id" not in column_names:
            connection.execute("""
                ALTER TABLE chat_records
                ADD COLUMN session_id TEXT NOT NULL DEFAULT 'default'
            """)
            print("已添加 session_id，旧记录归入 default 会话。")

        connection.commit()
    finally:
        connection.close()


def save_chat(question, answer, session_id):
    connection = sqlite3.connect(DB_PATH)

    try:
        cursor = connection.execute(
            """
            INSERT INTO chat_records (session_id, question, answer)
            VALUES (?, ?, ?)
            """,
            (session_id, question, answer),
        )
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def get_recent_chats(session_id="default"):
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.execute(
            """
            SELECT id, session_id, question, answer, created_at
            FROM chat_records
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT 5
            """,
            (session_id,),
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        connection.close()


if __name__ == "__main__":
    init_db()
    print("数据库初始化完成：", DB_PATH)

    records = get_recent_chats("default")
    print("default 会话最近的记录编号：",
          [record["id"] for record in records])