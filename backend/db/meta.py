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

    def getSyncHistoryCount(self, calendarId=None):
        if calendarId is not None:
            self.cursor.execute(
                'SELECT COUNT(*) FROM fetchlog WHERE calendarId = %s', (calendarId,)
            )
        else:
            self.cursor.execute('SELECT COUNT(*) FROM fetchlog')
        return self.cursor.fetchone()[0]

    def getSyncHistory(self, calendarId=None, page=1, pageSize=20):
        base = (
            'SELECT f.id, f.calendarId, r.calendarIdI18n, f.startTime, f.endTime, '
            'f.status, f.totalCourses, f.totalPages, f.msg, f.errorMessage '
            'FROM fetchlog f JOIN calendar_registry r ON f.calendarId = r.calendarId'
        )
        if calendarId is not None:
            self.cursor.execute(
                f'{base} WHERE f.calendarId = %s ORDER BY f.startTime DESC LIMIT %s OFFSET %s',
                (calendarId, pageSize, (page - 1) * pageSize)
            )
        else:
            self.cursor.execute(
                f'{base} ORDER BY f.startTime DESC LIMIT %s OFFSET %s',
                (pageSize, (page - 1) * pageSize)
            )
        return self.cursor.fetchall()

    def getSyncHistoryDetail(self, logId):
        self.cursor.execute(
            'SELECT f.id, f.calendarId, r.calendarIdI18n, f.startTime, f.endTime, '
            'f.status, f.totalCourses, f.totalPages, f.msg, f.errorMessage, f.fullLog '
            'FROM fetchlog f JOIN calendar_registry r ON f.calendarId = r.calendarId '
            'WHERE f.id = %s', (logId,)
        )
        return self.cursor.fetchone()
