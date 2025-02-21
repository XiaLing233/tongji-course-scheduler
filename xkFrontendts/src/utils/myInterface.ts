// occupy 三维数组一个单元的数据结构
export interface occupyCell {
    code: string;
    occupyWeek: number[];
}

// 课程安排
export interface arrangementInfolet {
    arrangementText: string;
    occupyDay: number;
    occupyTime: number[];
    occupyWeek: number[];
    occupyRoom: string;
    teacherAndCode: string;
}

// 教师
export interface teacherlet {
    teacherName: string;
    teacherCode: string;
}

// 课程详情
export interface courseDetaillet {
    arrangementInfo: arrangementInfolet[];
    campus: string;
    code: string;
    isExclusive?: boolean;
    status: number;
    teachers: teacherlet[];
    teachingLanguage: string;
}

// 课程信息，最上位的
export interface courseInfo {
    courseName: string;
    courseNameReserved: string;
    courseCode: string;
    courseType: string;
    credit: number;
    status: number,
    teacher: string[];
    courseDetail: courseDetaillet[];
}

// 专业信息
export interface baseInfoTriplet {
    calendarId: number;
    grade: number;
    major: string;
}

// 选修课类型
export interface optionalCourseType {
    courseLabelId: number;
    courseLabelName: string;
}
