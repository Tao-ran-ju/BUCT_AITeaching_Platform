"""临时脚本：dump buct_cip 各表行数 + 少量样本，用于对齐 ID 约定。"""
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
    cur.execute("SELECT COUNT(*) FROM `{}`".format(t))
    n = cur.fetchone()[0]
    print("=" * 90)
    print("TABLE: {}  (rows={})".format(t, n))
    cur.execute("SELECT * FROM `{}` LIMIT 3".format(t))
    cols = [d[0] for d in cur.description]
    print("  COLS:", cols)
    for row in cur.fetchall():
        print("  ", row)
conn.close()
