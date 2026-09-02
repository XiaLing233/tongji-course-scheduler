// 存放了选课状态的函数（已选、备选、未选 | 清除、退课..）

import { CourseStatus, type courseInfo } from "./myInterface";

export function defineStatus(courseInfo: courseInfo) : void {
    // 如果有备选的，不管是新选的还是改选的课，外层显示都是备选
    if (courseInfo.courseDetail.some(item => item.status === CourseStatus.Staged)) {
        courseInfo.status = CourseStatus.Staged; // 备选
    }
    else if (courseInfo.courseDetail.some(item => item.status === CourseStatus.Selected)) {
        courseInfo.status = CourseStatus.Selected; // 已选
    }
    else {
        courseInfo.status = CourseStatus.Unselected; // 未选
    }
}

export function defineAction(courseInfo: courseInfo) : string {
    if (courseInfo.courseDetail.some(item => item.status === CourseStatus.Selected)) {
        return "退课"; // 如果存在选课状态为已选的课程，那么显示退课，不管有没有未保存的改选
    }
    else {
        return "清除";
    }
}

export function mapStatusToChinese(status: number) : string {
    // console.log("status", status);
    switch (status) {
        case CourseStatus.Unselected:
            return "未选";
        case CourseStatus.Staged:
            return "备选";
        case CourseStatus.Selected:
            return "已选";
        default:
            return "未知";
    }
}

export function getTagColor(status: number) : string {
    switch (status) {
        case CourseStatus.Selected:
            return 'success';
        case CourseStatus.Staged:
            return 'warning';
        case CourseStatus.Unselected:
            return 'error';
        default:
            return 'default';
    }
}
