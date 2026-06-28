"""只读连接基类。calendar_id 模式走 DbRouter，否则直连元数据库。"""

import os

import mysql.connector

from .router import router


class ReadConnection:
    """MySQL 只读连接上下文。提供 self.db / self.cursor。"""

    def __init__(self, calendar_id=None):
        super().__init__()
        if calendar_id is not None:
            self.db = router.get_connection(calendar_id)
        else:
            self.db = mysql.connector.connect(
                host=os.getenv('DB_HOST'),
                user=os.getenv('DB_R_USER'),
                password=os.getenv('DB_R_PASSWORD'),
                database=os.getenv('DB_META'),
                port=int(os.getenv('DB_PORT')),
                charset='utf8mb4',
            )
        self.cursor = self.db.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cursor.close()
        self.db.close()
