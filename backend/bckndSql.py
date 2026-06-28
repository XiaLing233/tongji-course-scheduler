"""Backend 只读查询统一入口。bckndSql() → 元数据库, bckndSql(calendar_id=N) → 学期库。"""

from db.meta import MetaQueries
from db.course import CourseQueries


class bckndSql(MetaQueries, CourseQueries):
    """对外统一入口。"""
