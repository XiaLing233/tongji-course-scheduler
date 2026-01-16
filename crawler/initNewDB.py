import mysql.connector
import configparser
from datetime import datetime

# 读取配置文件
CONFIG = configparser.ConfigParser()
CONFIG.read('config.ini', encoding='utf-8')

# 设置数据库连接
DB_HOST = CONFIG['Sql']['host']
DB_USER = CONFIG['Sql']['user']
DB_R_USER = CONFIG['Sql']['r_user']
DB_PASSWORD = CONFIG['Sql']['password']
DB_NAME = CONFIG['Sql']['database']

def initNewDatabase(self):
    '''
    Initialize a new database
    '''

    # Connect to MySQL server
    connection = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
    )
    cursor = connection.cursor()

    # Create database if not exists
    new_db_name = DB_NAME

    print("DEBUG: Now creating new database:", new_db_name)

    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {new_db_name}")
    cursor.execute(f"USE {new_db_name}")

    # Grant privileges to user
    cursor.execute(f"GRANT SELECT ON {new_db_name}.* TO '{DB_R_USER}'@'localhost'")

    # Create tables
    with open('course_template.sql', 'r', encoding='utf-8') as f:
        sql_script = f.read()
        for statement in sql_script.split(';'):
            print("DEBUG: Executing statement:", statement)
            if statement.strip():
                cursor.execute(statement)

    connection.commit()
    cursor.close()
    connection.close()

    print(f"Database {new_db_name} initialized successfully.")

    return new_db_name


if __name__ == "__main__":
    initNewDatabase(None)
