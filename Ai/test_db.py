import sqlite3
import os

# 测试数据库连接和创建
def test_db():
    print(f"当前工作目录: {os.getcwd()}")
    
    # 尝试创建数据库
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()

    
    # 读取数据库内容
    print("\n数据库内容:")
    cursor.execute('SELECT * FROM chat_history')
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    
    conn.close()
    


if __name__ == "__main__":
    test_db()