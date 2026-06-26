"""元数据库只读查询 Mixin。"""

import json

from .connection import ReadConnection


class MetaQueries(ReadConnection):
    """元数据库查询方法。"""

    def getAllCalendar(self, limit=8):
        self.cursor.execute(
            'SELECT JSON_OBJECT("calendarId", calendarId, "calendarName", calendarIdI18n) '
            'FROM calendar_registry '
            'WHERE calendarIdI18n != \'数据同步中…\' '
            'ORDER BY calendarId DESC LIMIT %s', (limit,)
        )
        return [json.loads(row[0]) for row in self.cursor.fetchall()]

    def getLatestUpdateTime(self, calendarId=None):
        if calendarId is not None:
            self.cursor.execute(
                'SELECT startTime FROM fetchlog WHERE calendarId = %s '
                'ORDER BY startTime DESC LIMIT 1', (calendarId,)
            )
        else:
            self.cursor.execute(
                'SELECT startTime FROM fetchlog ORDER BY startTime DESC LIMIT 1'
            )
        rows = self.cursor.fetchall()
        return rows[0][0] if rows else None

    def getHealth(self):
        self.cursor.execute('SELECT 1')
        return self.cursor.fetchone()

    def getSyncHistory(self, calendarId=None, page=1, pageSize=20):
        base = ('SELECT id, calendarId, startTime, endTime, status, '
                'totalCourses, totalPages, msg, errorMessage FROM fetchlog')
        if calendarId is not None:
            self.cursor.execute(
                f'{base} WHERE calendarId = %s ORDER BY startTime DESC LIMIT %s OFFSET %s',
                (calendarId, pageSize, (page - 1) * pageSize)
            )
        else:
            self.cursor.execute(
                f'{base} ORDER BY startTime DESC LIMIT %s OFFSET %s',
                (pageSize, (page - 1) * pageSize)
            )
        return self.cursor.fetchall()

    def getSyncHistoryDetail(self, logId):
        self.cursor.execute(
            'SELECT id, calendarId, startTime, endTime, status, '
            'totalCourses, totalPages, msg, errorMessage, fullLog '
            'FROM fetchlog WHERE id = %s', (logId,)
        )
        return self.cursor.fetchone()
