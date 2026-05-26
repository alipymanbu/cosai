import sqlite3
import pandas as pd
import os

# 创建数据库连接
conn = sqlite3.connect('milk_tea_orders.db')
cursor = conn.cursor()

# 创建表结构
cursor.execute('''
CREATE TABLE IF NOT EXISTS milk_tea_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    日期 DATE,
    星期 TEXT,
    商品 TEXT,
    天气 TEXT,
    是否周末 BOOLEAN,
    是否促销 BOOLEAN,
    销量 INTEGER,
    客单价 INTEGER,
    销售额 INTEGER
)
''')

# 读取CSV数据
df = pd.read_csv('奶茶店每日订单.csv')

# 处理数据类型
df['是否周末'] = df['是否周末'].astype(bool)
df['是否促销'] = df['是否促销'].astype(bool)

# 导入数据到数据库
df.to_sql('milk_tea_orders', conn, if_exists='append', index=False)

# 验证数据导入情况
cursor.execute('SELECT COUNT(*) FROM milk_tea_orders')
count = cursor.fetchone()[0]
print(f"成功导入 {count} 条数据到数据库")

# 关闭连接
conn.close()
