"""临时脚本：dump buct_cip 库全部表的真实字段/索引，用于对齐 ORM 模型。

用法（凭据不写入本文件，通过环境变量传入）：
    DB_HOST=... DB_PORT=... DB_NAME=... DB_USER=... DB_PASSWORD=... python scripts/inspect_buct_cip.py
"""
import os

import pymysql

conn = pymysql.connect(
    host=os.environ["DB_HOST"],
    port=int(os.environ["DB_PORT"]),
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    database=os.environ["DB_NAME"],
    charset="utf8mb4",
    connect_timeout=15,
)
cur = conn.cursor()
cur.execute("SHOW TABLES")
tables = [r[0] for r in cur.fetchall()]
for t in tables:
    print("=" * 90)
    print("TABLE:", t)
    cur.execute("SHOW FULL COLUMNS FROM `{}`".format(t))
    for col in cur.fetchall():
        print("  {:<22} {:<24} null={:<3} key={:<4} default={:<12} extra={:<8} comment={}".format(
            col[0], col[1], col[3], col[4], str(col[5]), col[6], col[8]))
    cur.execute("SHOW INDEX FROM `{}`".format(t))
    idx = {}
    for r in cur.fetchall():
        key = r[2]
        idx.setdefault(key, []).append((r[3], r[4]))
    for k, cols in idx.items():
        cols.sort()
        print("    IDX {}: {}".format(k, ", ".join(c[1] for c in cols)))
conn.close()
