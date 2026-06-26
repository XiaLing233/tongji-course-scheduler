"""tjSql — 统一入口，组合 Connection + CourseInserter + BlueGreen + FetchLogger。"""

from db.connection import Connection
from db.inserter import CourseInserter
from db.bluegreen import BlueGreen
from db.log import FetchLogger


class tjSql(Connection, CourseInserter, BlueGreen, FetchLogger):
    """对外统一入口。"""
