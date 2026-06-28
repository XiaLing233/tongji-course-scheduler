"""共享测试数据 — 真实 arrangeInfo 样本 + DB 集成测试 fixture。"""

import os
import time

import mysql.connector
import pytest
from mysql.connector.errors import DatabaseError


def _connect_with_retry(config, max_retries=10, delay=2):
    """连接 MySQL，失败时重试（应对容器初始化后短暂重启窗口）。"""
    for i in range(max_retries):
        try:
            return mysql.connector.connect(**config)
        except DatabaseError:
            if i == max_retries - 1:
                raise
            time.sleep(delay)

# ================================================================
#  DB 集成测试 fixture — 独立测试数据库
# ================================================================

TEST_META = 'test_course_scheduler_meta'
TEST_CAL_ID = 999
TEST_CAL_A = f'calendar_{TEST_CAL_ID}_a'
TEST_CAL_B = f'calendar_{TEST_CAL_ID}_b'

_META_DDL = """
CREATE TABLE IF NOT EXISTS `calendar_registry` (
  `calendarId` int NOT NULL,
  `calendarIdI18n` varchar(200) NOT NULL,
  `active_suffix` char(1) NOT NULL DEFAULT 'a',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`calendarId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE VIEW `active_calendars` AS
SELECT `calendarId`, `calendarIdI18n`,
  CONCAT('calendar_', `calendarId`, '_', `active_suffix`) AS `db_name`,
  `active_suffix`, `updated_at`
FROM `calendar_registry`;
CREATE TABLE `fetchlog` (
  `id` int NOT NULL AUTO_INCREMENT,
  `calendarId` int NOT NULL,
  `startTime` datetime(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `endTime` datetime(3) DEFAULT NULL,
  `status` enum('running','completed','failed') NOT NULL DEFAULT 'running',
  `totalCourses` int DEFAULT 0, `totalPages` int DEFAULT 0,
  `msg` varchar(500) DEFAULT NULL, `errorMessage` text, `fullLog` mediumtext,
  PRIMARY KEY (`id`), KEY `idx_fetchlog_time` (`startTime`),
  CONSTRAINT `fk_fetchlog_calendar` FOREIGN KEY (`calendarId`) REFERENCES `calendar_registry` (`calendarId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
"""
_COURSE_DDL = """
CREATE TABLE IF NOT EXISTS `assessment` (
  `assessmentMode` varchar(200) NOT NULL, `assessmentModeI18n` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`assessmentMode`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE TABLE IF NOT EXISTS `campus` (
  `campus` varchar(200) NOT NULL, `campusI18n` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`campus`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE TABLE IF NOT EXISTS `coursenature` (
  `courseLabelId` int NOT NULL, `courseLabelName` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`courseLabelId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE TABLE IF NOT EXISTS `faculty` (
  `faculty` varchar(200) NOT NULL, `facultyI18n` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`faculty`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE TABLE IF NOT EXISTS `language` (
  `teachingLanguage` varchar(200) NOT NULL,
  `teachingLanguageI18n` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`teachingLanguage`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE TABLE IF NOT EXISTS `major` (
  `id` int NOT NULL AUTO_INCREMENT, `code` varchar(200) DEFAULT NULL,
  `grade` int DEFAULT NULL, `name` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE TABLE IF NOT EXISTS `coursedetail` (
  `id` bigint NOT NULL, `code` varchar(200) DEFAULT NULL,
  `name` TEXT DEFAULT NULL, `courseLabelId` int DEFAULT NULL,
  `assessmentMode` varchar(200) DEFAULT NULL, `period` int DEFAULT NULL,
  `weekHour` int DEFAULT NULL, `campus` varchar(200) DEFAULT NULL,
  `number` int DEFAULT NULL, `elcNumber` int DEFAULT NULL,
  `startWeek` int DEFAULT NULL, `endWeek` int DEFAULT NULL,
  `courseCode` varchar(200) DEFAULT NULL, `courseName` varchar(200) DEFAULT NULL,
  `credit` double DEFAULT NULL, `teachingLanguage` varchar(200) DEFAULT NULL,
  `faculty` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `nature_idx` (`courseLabelId`), KEY `assess_idx` (`assessmentMode`),
  KEY `campusKey_idx` (`campus`), KEY `facultyKey_idx` (`faculty`),
  KEY `langKey_idx` (`teachingLanguage`),
  CONSTRAINT `assessKey` FOREIGN KEY (`assessmentMode`) REFERENCES `assessment` (`assessmentMode`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `campusKey` FOREIGN KEY (`campus`) REFERENCES `campus` (`campus`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `facultyKey` FOREIGN KEY (`faculty`) REFERENCES `faculty` (`faculty`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `langKey` FOREIGN KEY (`teachingLanguage`) REFERENCES `language` (`teachingLanguage`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `natureKey` FOREIGN KEY (`courseLabelId`) REFERENCES `coursenature` (`courseLabelId`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE TABLE IF NOT EXISTS `majorandcourse` (
  `id` int NOT NULL AUTO_INCREMENT, `majorId` int NOT NULL, `courseId` bigint NOT NULL,
  PRIMARY KEY (`id`), KEY `courseKey_idx` (`courseId`), KEY `majorKeyForMajor_idx` (`majorId`),
  CONSTRAINT `courseKeyForMajor` FOREIGN KEY (`courseId`) REFERENCES `coursedetail` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `majorKeyForMajor` FOREIGN KEY (`majorId`) REFERENCES `major` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE TABLE IF NOT EXISTS `teacher` (
  `id` bigint NOT NULL, `teachingClassId` bigint DEFAULT NULL,
  `teacherCode` varchar(200) DEFAULT NULL, `teacherName` varchar(200) DEFAULT NULL,
  `arrangeInfoText` mediumtext,
  PRIMARY KEY (`id`), KEY `classKey_idx` (`teachingClassId`),
  CONSTRAINT `courseKey` FOREIGN KEY (`teachingClassId`) REFERENCES `coursedetail` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
"""


def _get_db_config(database=None):
    return {
        'host': os.getenv('DB_HOST', 'mysql'),
        'port': int(os.getenv('DB_PORT', '3306')),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': database, 'charset': 'utf8mb4',
    }


def _exec_ddl(conn, ddl):
    c = conn.cursor()
    for stmt in ddl.split(';'):
        stmt = stmt.strip()
        if stmt:
            c.execute(stmt)
    conn.commit()


@pytest.fixture(scope='session')
def db_config():
    return _get_db_config()


@pytest.fixture(scope='session')
def test_meta_conn(db_config):
    cfg = {**db_config}
    conn = _connect_with_retry(cfg)
    c = conn.cursor()
    c.execute(f"CREATE DATABASE IF NOT EXISTS `{TEST_META}` "
              "CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci")
    conn.commit(); conn.close()
    conn = _connect_with_retry({**cfg, 'database': TEST_META})
    _exec_ddl(conn, _META_DDL)
    c = conn.cursor()
    c.execute("INSERT INTO calendar_registry (calendarId, calendarIdI18n) "
              f"VALUES ({TEST_CAL_ID}, '测试学期-A面活跃')")
    conn.commit()
    yield conn
    c = conn.cursor()
    for db_name in [TEST_META, TEST_CAL_A, TEST_CAL_B]:
        c.execute(f"DROP DATABASE IF EXISTS `{db_name}`")
    conn.commit(); conn.close()


@pytest.fixture(scope='session')
def test_cal_a_conn(db_config, test_meta_conn):
    conn = _connect_with_retry({**db_config})
    c = conn.cursor()
    c.execute(f"CREATE DATABASE IF NOT EXISTS `{TEST_CAL_A}` "
              "CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci")
    conn.commit(); conn.close()
    conn = mysql.connector.connect(**{**db_config, 'database': TEST_CAL_A})
    _exec_ddl(conn, _COURSE_DDL)
    yield conn; conn.close()


@pytest.fixture
def patch_env(monkeypatch):
    monkeypatch.setenv('DB_META', TEST_META)
    monkeypatch.setenv('DB_R_USER', os.getenv('DB_USER', 'root'))
    monkeypatch.setenv('DB_R_PASSWORD', os.getenv('DB_PASSWORD', ''))
    # 清 mysql-connector-python 全局 pool 注册表 + DbRouter 缓存
    from mysql.connector.pooling import _CONNECTION_POOLS
    _CONNECTION_POOLS.clear()
    from db.router import router
    router._pools.clear()
    router._meta_pool = None


# ================================================================
#  ArrangeInfo 样本 fixture
# ================================================================


# ================================================================
#  正常格式 — 单教师、单时间段
# ================================================================

@pytest.fixture
def sample_normal():
    """标准同济格式：Name(Code) 星期 + 节次 + 周次 + 教室"""
    return "王鑫(21075) 星期六7-8节 [1-15单] 线上教室"


@pytest.fixture
def sample_multi_teacher():
    """多教师逗号分隔"""
    return "李姣(07085),高芙蓉(10017) 星期一1-2节 [15] 沪西二教135阶梯教室"


@pytest.fixture
def sample_many_teachers():
    """8 人教师团"""
    return ("惠英(01022),张兰芳(01027),暨育雄(12067),朱炜(13162),"
            "余博(21051),王鹏玲(21058),邢莹莹(21149),Mohsen Alae(24076) "
            "星期三9-10节 [1-16] 博楼B106")


@pytest.fixture
def sample_fudan():
    """复旦格式：只有工号没有姓名（旧数据，修复前）"""
    return "(2400162),李奕滨(94431) 星期三10-11节 [1-16] 复旦三教208"


@pytest.fixture
def sample_fudan_fixed():
    """复旦格式：已补全姓名（修复后）"""
    return ("寇宗来(2400162),李奕滨(94431) 星期三10-11节 [1-16] "
            "复旦三教208(单周三)；线上(双周三)；复旦五教116、106、114(周五讨论)")


# ================================================================
#  周次边缘情况
# ================================================================

@pytest.fixture
def sample_odd_week():
    """单周"""
    return "唐克双(11067) 星期二1-2节 [1-7单] 诚楼C411"


@pytest.fixture
def sample_even_week():
    """双周"""
    return "王平(16162) 星期三1-2节 [2-16双] 南310"


@pytest.fixture
def sample_mixed_odd_even():
    """单双周混合"""
    return ("尹岚(05158),杨红(09110),高山峨(09165),安毛毛(13144),"
            "张明(18524),杨健(19605) 星期三1-2节 [11-13单 14-16双] 沪西二教122大教室")


@pytest.fixture
def sample_space_separated_weeks():
    """空格分隔的离散周次"""
    return "高芙蓉(10017) 星期五1-2节 [1 4] 沪西二教135阶梯教室"


@pytest.fixture
def sample_single_range():
    """单节范围 3-3节"""
    return "高芙蓉(10017) 星期三3-3节 [4] 沪西二教135阶梯教室"


# ================================================================
#  节次 & 学期模式
# ================================================================

@pytest.fixture
def sample_9_11_periods():
    """9-11 节（长时段）"""
    return "叶建锋(22019) 星期三9-11节 [1-16] 南222"


@pytest.fixture
def sample_9_10_new_system():
    """11节课制：9-10 节（calendarId >= 120）"""
    return "田唯佳(14167) 星期一9-10节 [1-16] 南101"


# ================================================================
#  旧学期（17 周制）— calendarId < 120
# ================================================================

@pytest.fixture
def sample_17weeks():
    """17 周满学期（旧制，如 2024-2025学年）"""
    return "左琰(91129) 星期三7-8节 [1-17] 北105"


@pytest.fixture
def sample_17weeks_odd():
    """17 周单周（1-17单）"""
    return "梅萌(00789) 星期二3-4节 [1-17单] 安楼A305"


@pytest.fixture
def sample_17weeks_mixed():
    """混合：空间分隔 + 单周（1-7 15-17单）"""
    return "颜文涛(17022) 星期三3-4节 [1-7 15-17单] 北313"


@pytest.fixture
def sample_17weeks_multiline():
    """17 周制多行排课（普通 + 单周混合）"""
    return ("李慕君(10039) 星期一7-8节 [2-17] 博楼B310\n"
            "李慕君(10039) 星期四5-6节 [1-17单] 博楼B310\n")


# ================================================================
#  多行排课
# ================================================================

@pytest.fixture
def sample_multiline():
    """一个教师的多时间段排课（\n 分隔）"""
    return ("周玥(20154) 星期一3-4节 [1-16] 口院临床\n"
            "周玥(20154) 星期二1-4节 [1-16] 口院临床\n"
            "周玥(20154) 星期三1-2节 [1-16] 口院临床\n"
            "周玥(20154) 星期四5-8节 [1-16] 口院临床\n"
            "周玥(20154) 星期五1-8节 [1-16] 口院临床\n")


@pytest.fixture
def sample_multiline_multi_teacher():
    """多教师 + 多时间段（部分时间段教师组合不同）"""
    return ("高芙蓉(10017) 星期一1-2节 [2-3] 沪西二教135阶梯教室\n"
            "李姣(07085),高芙蓉(10017) 星期一1-2节 [15] 沪西二教135阶梯教室\n"
            "高芙蓉(10017) 星期一1-1节 [1] 沪西二教135阶梯教室\n"
            "高芙蓉(10017) 星期三3-4节 [1-3] 沪西二教135阶梯教室\n"
            "李姣(07085),高芙蓉(10017) 星期三3-4节 [15] 沪西二教135阶梯教室\n"
            "高芙蓉(10017) 星期三3-3节 [4] 沪西二教135阶梯教室\n"
            "高芙蓉(10017) 星期五1-2节 [1 4] 沪西二教135阶梯教室\n")


# ================================================================
#  教室特殊格式
# ================================================================

@pytest.fixture
def sample_no_classroom():
    """教室字段为非标准文本"""
    return "郭为安(14015) 星期五5-6节 [1-16] 德国学校学习"


@pytest.fixture
def sample_fudan_complex_room():
    """复旦课程：教室含中文括号和分号"""
    return ("寇宗来(2400162),李奕滨(94431) 星期三10-11节 [1-16] "
            "复旦三教208(单周三)；线上(双周三)；复旦五教116、106、114(周五讨论)")


# ================================================================
#  边界情况 — 空 / 异常输入
# ================================================================

@pytest.fixture
def sample_empty():
    return ""


@pytest.fixture
def sample_none():
    return None


# ================================================================
#  optCourseQueryListGenerator 参数集
# ================================================================

@pytest.fixture
def query_old_system_cases():
    """12 节课制（calendarId < 120）的 (day, section, expected)"""
    return [
        # section 1-4 → X-Y节 模式
        (1, 1, "%星期一1-2%"),
        (2, 2, "%星期二3-4%"),
        (3, 3, "%星期三5-6%"),
        (4, 4, "%星期四7-8%"),
        # section 5 → 第9节
        (5, 5, "%星期五9-%"),
        # section 6 → 10-12节
        (6, 6, "%星期六10-1_%"),
        # 星期天
        (7, 1, "%星期日1-2%"),
    ]


@pytest.fixture
def query_new_system_cases():
    """11 节课制（calendarId >= 120）的 (day, section, expected)"""
    return [
        # section 1-4 → X-Y节 模式（同旧制）
        (1, 1, "%星期一1-2%"),
        (2, 2, "%星期二3-4%"),
        (3, 3, "%星期三5-6%"),
        (4, 4, "%星期四7-8%"),
        # section 5 → 9-10节
        (5, 5, "%星期五9-1_%"),
        # section 6 → 11节
        (6, 6, "%星期六_-11%"),
    ]


@pytest.fixture
def query_boundary_cases():
    """无效输入应返回 None"""
    return [
        (1, 7, 119),   # section 7 无效
        (1, 0, 120),   # section 0 无效
        (1, 7, 120),   # section 7 无效（新制）
    ]
