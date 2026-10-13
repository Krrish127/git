import sqlite3
from pathlib import Path

# 数据库文件固定放在当前代码文件旁边。
db_path = Path(__file__).resolve().parent / "customers.db"

# 连接数据库；文件不存在时会创建。
connection = sqlite3.connect(str(db_path))

try:
    # 创建客户表；已经存在时不重复创建。
    connection.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            industry TEXT NOT NULL
        )
    """)

    # 用参数传入数据。
    connection.execute(
        "INSERT INTO customers (name, industry) VALUES (?, ?)",
        ("甲公司", "制造业"),
    )

    # 提交写入。
    connection.commit()

    # 查询所有客户，按编号排序。
    cursor = connection.execute(
        "SELECT id, name, industry FROM customers ORDER BY id"
    )
    rows = cursor.fetchall()

    for row in rows:
        print(row)

finally:
    connection.close()