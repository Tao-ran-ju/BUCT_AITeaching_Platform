import pymysql

# 数据库配置
OJ_DB_CONFIG = {
    'host': '222.199.230.149',
    'port': 3306,
    'user': 'gjr',
    'password': 'gjr2024040022',
    'database': 'jol',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def query_mysql():
    connection = None
    try:
        # 建立连接
        connection = pymysql.connect(**OJ_DB_CONFIG)
        cursor = connection.cursor()

        # 1. 查看当前数据库所有表
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        print("=== 当前 jol 库所有表 ===")
        for table in tables:
            print(table[f'Tables_in_{OJ_DB_CONFIG["database"]}'])

        # 2. 示例：查询某张表全部数据（把table_name替换成真实表名）
        table_name = "替换成上面打印出来的表名"
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 100;")
        rows = cursor.fetchall()
        print(f"\n=== 表 {table_name} 前100条数据 ===")
        for row in rows:
            print(row)

    except pymysql.MySQLError as e:
        print(f"数据库连接/查询失败：{e}")
    finally:
        # 关闭连接
        if connection and connection.open:
            connection.close()
            print("\n数据库连接已关闭")

if __name__ == "__main__":
    query_mysql()