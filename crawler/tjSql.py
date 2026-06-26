"""tjSql — 统一入口，组合 CourseInserter + BlueGreen + FetchLogger（均继承 Connection）。"""

from db.inserter import CourseInserter
from db.bluegreen import BlueGreen
from db.log import FetchLogger


class tjSql(CourseInserter, BlueGreen, FetchLogger):
    """对外统一入口。"""
