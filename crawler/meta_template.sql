-- ============================================================
-- 元数据库 course_scheduler_meta — 学期注册表 + 同步日志
-- 蓝绿部署：每学期独立数据库，由 active_suffix 控制路由
-- MySQL docker-entrypoint-initdb.d 会自动执行此脚本
-- ============================================================

CREATE DATABASE IF NOT EXISTS `course_scheduler_meta`
  CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

USE `course_scheduler_meta`;

CREATE TABLE `calendar_registry` (
  `calendarId` int NOT NULL,
  `calendarIdI18n` varchar(200) NOT NULL,
  `active_suffix` char(1) NOT NULL DEFAULT 'a',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`calendarId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 视图：自动解析当前活跃数据库名
-- 用法: SELECT db_name FROM active_calendars WHERE calendarId = 121
CREATE VIEW `active_calendars` AS
SELECT
  `calendarId`,
  `calendarIdI18n`,
  CONCAT('calendar_', `calendarId`, '_', `active_suffix`) AS `db_name`,
  `active_suffix`,
  `updated_at`
FROM `calendar_registry`;

CREATE TABLE `fetchlog` (
  `id` int NOT NULL AUTO_INCREMENT,
  `calendarId` int NOT NULL,
  `startTime` datetime(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `endTime` datetime(3) DEFAULT NULL,
  `status` enum('running','completed','failed') NOT NULL DEFAULT 'running',
  `totalCourses` int DEFAULT 0,
  `totalPages` int DEFAULT 0,
  `msg` varchar(500) DEFAULT NULL,
  `errorMessage` text,
  `fullLog` mediumtext,
  PRIMARY KEY (`id`),
  KEY `idx_fetchlog_time` (`startTime`),
  CONSTRAINT `fk_fetchlog_calendar` FOREIGN KEY (`calendarId`) REFERENCES `calendar_registry` (`calendarId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
