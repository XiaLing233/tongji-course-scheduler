"""US-5.2 — Crawler 集成测试 fixture。独立测试数据库，不污染开发数据。"""

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

TEST_META = 'test_course_scheduler_meta'
TEST_CAL_ID = 999
TEST_CAL_A = f'calendar_{TEST_CAL_ID}_a'
TEST_CAL_B = f'calendar_{TEST_CAL_ID}_b'
TEST_CAL_NEW = 998


def _get_db_config(database=None):
    return {
        'host': os.getenv('DB_HOST', 'mysql'),
        'port': int(os.getenv('DB_PORT', '3306')),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': database,
        'charset': 'utf8mb4',
    }


def _execute_sql(conn, sql):
    c = conn.cursor()
    for stmt in sql.split(';'):
        stmt = stmt.strip()
        if stmt:
            c.execute(stmt)
    conn.commit()


@pytest.fixture(scope='session')
def db_config():
    return _get_db_config()


@pytest.fixture(scope='session')
def test_meta_conn(db_config):
    """创建 test_course_scheduler_meta 并注册测试学期。"""
    cfg = {**db_config}
    conn = _connect_with_retry(cfg)
    c = conn.cursor()
    c.execute(f"CREATE DATABASE IF NOT EXISTS `{TEST_META}` "
              "CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci")
    conn.commit()
    conn.close()

    conn = _connect_with_retry({**cfg, 'database': TEST_META})
    _META_DDL = """
CREATE TABLE IF NOT EXISTS `calendar_registry` (
  `calendarId` int NOT NULL,
  `calendarIdI18n` varchar(200) NOT NULL,
  `active_suffix` char(1) NOT NULL DEFAULT 'a',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`calendarId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE OR REPLACE VIEW `active_calendars` AS
SELECT `calendarId`, `calendarIdI18n`,
  CONCAT('calendar_', `calendarId`, '_', `active_suffix`) AS `db_name`,
  `active_suffix`, `updated_at`
FROM `calendar_registry`;
CREATE TABLE IF NOT EXISTS `fetchlog` (
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
    _execute_sql(conn, _META_DDL)

    c = conn.cursor()
    c.execute(
        "INSERT INTO calendar_registry (calendarId, calendarIdI18n) "
        f"VALUES ({TEST_CAL_ID}, '测试学期-A面活跃') "
        "ON DUPLICATE KEY UPDATE calendarIdI18n=calendarIdI18n"
    )
    conn.commit()
    yield conn

    c = conn.cursor()
    for db_name in [TEST_META, TEST_CAL_A, TEST_CAL_B,
                    f'calendar_{TEST_CAL_NEW}_a',
                    f'calendar_{TEST_CAL_NEW}_b']:
        c.execute(f"DROP DATABASE IF EXISTS `{db_name}`")
    conn.commit()
    conn.close()


_COURSE_DDL = """
CREATE TABLE IF NOT EXISTS `assessment` (
  `assessmentMode` varchar(200) NOT NULL,
  `assessmentModeI18n` varchar(200) DEFAULT NULL,
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
  `faculty` varchar(200) DEFAULT NULL, `newCourseCode` varchar(200) DEFAULT NULL,
  `newCode` varchar(200) DEFAULT NULL,
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


def _create_cal_db(db_config, db_name):
    conn = _connect_with_retry({**db_config})
    c = conn.cursor()
    c.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
              "CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci")
    conn.commit(); conn.close()
    conn = _connect_with_retry({**db_config, 'database': db_name})
    _execute_sql(conn, _COURSE_DDL)
    return conn


@pytest.fixture(scope='session')
def test_cal_a_conn(db_config, test_meta_conn):
    conn = _create_cal_db(db_config, TEST_CAL_A)
    yield conn
    conn.close()


@pytest.fixture(scope='session')
def test_cal_b_conn(db_config, test_meta_conn):
    conn = _create_cal_db(db_config, TEST_CAL_B)
    yield conn
    conn.close()


@pytest.fixture(autouse=True)
def clean_cal_tables(test_cal_a_conn, test_cal_b_conn):
    """每个测试前 TRUNCATE。"""
    for conn in [test_cal_a_conn, test_cal_b_conn]:
        c = conn.cursor()
        c.execute("SET FOREIGN_KEY_CHECKS = 0")
        for table in ('majorandcourse', 'teacher', 'coursedetail',
                      'major', 'language', 'faculty', 'coursenature', 'campus', 'assessment'):
            c.execute(f"TRUNCATE TABLE {table}")
        c.execute("SET FOREIGN_KEY_CHECKS = 1")
        conn.commit()


@pytest.fixture
def patch_env(monkeypatch):
    """env 切到测试数据库。"""
    monkeypatch.setenv('DB_META', TEST_META)
    monkeypatch.setenv('DB_R_USER', os.getenv('DB_USER', 'root'))
    monkeypatch.setenv('DB_R_PASSWORD', os.getenv('DB_PASSWORD', ''))
