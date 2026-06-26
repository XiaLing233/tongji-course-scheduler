"""同步日志 — startFetchLog / finishFetchLog。"""

from db.connection import Connection


class FetchLogger(Connection):
    """写入元数据库 fetchlog 表。"""

    def startFetchLog(self, calendarId, msg=''):
        """INSERT running 状态 → 返回 fetchlog ID。"""
        self._use_meta()
        self.cursor.execute(
            "INSERT INTO fetchlog (calendarId, startTime, status, msg) "
            "VALUES (%s, NOW(3), 'running', %s)",
            (calendarId, msg)
        )
        self.db.commit()
        return self.cursor.lastrowid

    def finishFetchLog(self, fetchlog_id, status='completed', totalCourses=0,
                       totalPages=0, errorMessage=None, fullLog=None):
        """UPDATE 为 completed 或 failed。"""
        self._use_meta()
        if status == 'completed':
            self.cursor.execute(
                "UPDATE fetchlog SET status='completed', endTime=NOW(3), "
                "totalCourses=%s, totalPages=%s, fullLog=%s WHERE id=%s",
                (totalCourses, totalPages, fullLog, fetchlog_id)
            )
        else:
            self.cursor.execute(
                "UPDATE fetchlog SET status='failed', endTime=NOW(3), "
                "errorMessage=%s WHERE id=%s",
                (errorMessage, fetchlog_id)
            )
        self.db.commit()
