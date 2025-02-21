// 存放了选课状态的函数（已选、备选、未选 | 清除、退课..）

import { courseInfo } from "./myInterface";

export function defineStatus(courseInfo: courseInfo) : void {
    // 如果有备选的，不管是新选的还是改选的课，外层显示都是备选
    if (courseInfo.courseDetail.some(item => item.status === 1)) {
        courseInfo.status = 1; // 备选
    }
    else if (courseInfo.courseDetail.some(item => item.status === 2)) {
        courseInfo.status = 2; // 已选
    }
    else {
        courseInfo.status = 0; // 未选
    }
}

export function defineAction(courseInfo: courseInfo) : string {
    if (courseInfo.courseDetail.some(item => item.status === 2)) {
        return "退课"; // 如果存在选课状态为已选的课程，那么显示退课，不管有没有未保存的改选
    }
    else {
        return "清除";
    }
}

export function deleteSelectedCourse(selectedCourses : string[], code: string) : string[] {
    return selectedCourses.filter(item => item !== code);
}

export function deleteStagedCourse()