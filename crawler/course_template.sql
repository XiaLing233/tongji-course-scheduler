-- ============================================================
-- 学期库模板 — 每个 calendar_{id}_{suffix} 数据库使用此 DDL
-- 与旧 schema 的区别:
--   1. 移除 calendar 表 (由元数据库 calendar_registry 替代)
--   2. 移除所有表的 calendarId 列、外键、索引
--   3. 移除 fetchlog 表 (移至元数据库)
--   4. langKey FK 补齐 CASCADE (与其余维度表一致)
-- ============================================================

CREATE TABLE `assessment` (
  `assessmentMode` varchar(200) NOT NULL,
  `assessmentModeI18n` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`assessmentMode`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `campus` (
  `campus` varchar(200) NOT NULL,
  `campusI18n` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`campus`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `coursenature` (
  `courseLabelId` int NOT NULL,
  `courseLabelName` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`courseLabelId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `faculty` (
  `faculty` varchar(200) NOT NULL,
  `facultyI18n` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`faculty`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `language` (
  `teachingLanguage` varchar(200) NOT NULL,
  `teachingLanguageI18n` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`teachingLanguage`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `major` (
  `id` int NOT NULL AUTO_INCREMENT,
  `code` varchar(200) DEFAULT NULL,
  `grade` int DEFAULT NULL,
  `name` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `major_code_grade_idx` (`code`, `grade`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `coursedetail` (
  `id` bigint NOT NULL,
  `code` varchar(200) DEFAULT NULL,
  `name` TEXT DEFAULT NULL,
  `courseLabelId` int DEFAULT NULL,
  `assessmentMode` varchar(200) DEFAULT NULL,
  `period` int DEFAULT NULL,
  `weekHour` int DEFAULT NULL,
  `campus` varchar(200) DEFAULT NULL,
  `number` int DEFAULT NULL,
  `elcNumber` int DEFAULT NULL,
  `startWeek` int DEFAULT NULL,
  `endWeek` int DEFAULT NULL,
  `courseCode` varchar(200) DEFAULT NULL,
  `courseName` varchar(200) DEFAULT NULL,
  `credit` double DEFAULT NULL,
  `teachingLanguage` varchar(200) DEFAULT NULL,
  `faculty` varchar(200) DEFAULT NULL,
  `newCourseCode` varchar(200) DEFAULT NULL,
  `newCode` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `nature_idx` (`courseLabelId`),
  KEY `assess_idx` (`assessmentMode`),
  KEY `campusKey_idx` (`campus`),
  KEY `facultyKey_idx` (`faculty`),
  KEY `langKey_idx` (`teachingLanguage`),
  KEY `courseCode_idx` (`courseCode`),
  CONSTRAINT `assessKey` FOREIGN KEY (`assessmentMode`) REFERENCES `assessment` (`assessmentMode`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `campusKey` FOREIGN KEY (`campus`) REFERENCES `campus` (`campus`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `facultyKey` FOREIGN KEY (`faculty`) REFERENCES `faculty` (`faculty`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `langKey` FOREIGN KEY (`teachingLanguage`) REFERENCES `language` (`teachingLanguage`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `natureKey` FOREIGN KEY (`courseLabelId`) REFERENCES `coursenature` (`courseLabelId`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `majorandcourse` (
  `id` int NOT NULL AUTO_INCREMENT,
  `majorId` int NOT NULL,
  `courseId` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `courseKey_idx` (`courseId`),
  KEY `majorKeyForMajor_idx` (`majorId`),
  KEY `course_major_idx` (`courseId`, `majorId`),
  CONSTRAINT `courseKeyForMajor` FOREIGN KEY (`courseId`) REFERENCES `coursedetail` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `majorKeyForMajor` FOREIGN KEY (`majorId`) REFERENCES `major` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `teacher` (
  `id` bigint NOT NULL,
  `teachingClassId` bigint DEFAULT NULL,
  `teacherCode` varchar(200) DEFAULT NULL,
  `teacherName` varchar(200) DEFAULT NULL,
  `arrangeInfoText` mediumtext,
  PRIMARY KEY (`id`),
  KEY `classKey_idx` (`teachingClassId`),
  KEY `teacherName_idx` (`teacherName`),
  KEY `teacherCode_idx` (`teacherCode`),
  CONSTRAINT `courseKey` FOREIGN KEY (`teachingClassId`) REFERENCES `coursedetail` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
