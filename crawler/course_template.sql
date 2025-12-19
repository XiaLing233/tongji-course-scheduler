CREATE TABLE `assessment` (
  `assessmentMode` varchar(45) NOT NULL,
  `assessmentModeI18n` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`assessmentMode`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `calendar` (
  `calendarId` int NOT NULL,
  `calendarIdI18n` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`calendarId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `campus` (
  `campus` varchar(45) NOT NULL,
  `campusI18n` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`campus`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `coursenature` (
  `courseLabelId` int NOT NULL,
  `courseLabelName` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`courseLabelId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `faculty` (
  `faculty` varchar(45) NOT NULL,
  `facultyI18n` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`faculty`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `fetchlog` (
  `id` int NOT NULL AUTO_INCREMENT,
  `fetchTime` datetime DEFAULT NULL,
  `msg` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `language` (
  `teachingLanguage` varchar(45) NOT NULL,
  `teachingLanguageI18n` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`teachingLanguage`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `major` (
  `id` int NOT NULL AUTO_INCREMENT,
  `code` varchar(45) DEFAULT NULL,
  `grade` int DEFAULT NULL,
  `name` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1116 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `coursedetail` (
  `id` bigint NOT NULL,
  `code` varchar(45) DEFAULT NULL,
  `name` varchar(45) DEFAULT NULL,
  `courseLabelId` int DEFAULT NULL,
  `assessmentMode` varchar(45) DEFAULT NULL,
  `period` int DEFAULT NULL,
  `weekHour` int DEFAULT NULL,
  `campus` varchar(45) DEFAULT NULL,
  `number` int DEFAULT NULL,
  `elcNumber` int DEFAULT NULL,
  `startWeek` int DEFAULT NULL,
  `endWeek` int DEFAULT NULL,
  `courseCode` varchar(45) DEFAULT NULL,
  `courseName` varchar(45) DEFAULT NULL,
  `credit` double DEFAULT NULL,
  `teachingLanguage` varchar(45) DEFAULT NULL,
  `faculty` varchar(45) DEFAULT NULL,
  `calendarId` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `nature_idx` (`courseLabelId`),
  KEY `assess_idx` (`assessmentMode`),
  KEY `campusKey_idx` (`campus`),
  KEY `facultyKey_idx` (`faculty`),
  KEY `calendarKey_idx` (`calendarId`),
  KEY `langKey_idx` (`teachingLanguage`),
  CONSTRAINT `assessKey` FOREIGN KEY (`assessmentMode`) REFERENCES `assessment` (`assessmentMode`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `calendarKey` FOREIGN KEY (`calendarId`) REFERENCES `calendar` (`calendarId`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `campusKey` FOREIGN KEY (`campus`) REFERENCES `campus` (`campus`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `facultyKey` FOREIGN KEY (`faculty`) REFERENCES `faculty` (`faculty`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `langKey` FOREIGN KEY (`teachingLanguage`) REFERENCES `language` (`teachingLanguage`),
  CONSTRAINT `natureKey` FOREIGN KEY (`courseLabelId`) REFERENCES `coursenature` (`courseLabelId`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `majorandcourse` (
  `id` int NOT NULL AUTO_INCREMENT,
  `majorId` int NOT NULL,
  `courseId` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `courseKey_idx` (`courseId`),
  KEY `majorKeyForMajor_idx` (`majorId`),
  CONSTRAINT `courseKeyForMajor` FOREIGN KEY (`courseId`) REFERENCES `coursedetail` (`id`),
  CONSTRAINT `majorKeyForMajor` FOREIGN KEY (`majorId`) REFERENCES `major` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=82013 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `teacher` (
  `id` bigint NOT NULL,
  `teachingClassId` bigint DEFAULT NULL,
  `teacherCode` varchar(45) DEFAULT NULL,
  `teacherName` varchar(100) DEFAULT NULL,
  `arrangeInfoText` mediumtext,
  PRIMARY KEY (`id`),
  KEY `classKey_idx` (`teachingClassId`),
  CONSTRAINT `courseKey` FOREIGN KEY (`teachingClassId`) REFERENCES `coursedetail` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
