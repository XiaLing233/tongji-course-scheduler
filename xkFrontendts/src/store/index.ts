import { createStore } from "vuex";
import { canAddCourse, insertOccupied, deleteOccupied, isSameCourse } from "@/utils/courseManipulate";
import type { courseDetaillet, baseInfoTriplet, courseInfo } from "@/utils/myInterface";

const store = createStore({
    state() {
        return {
            // 检索的基本信息
            majorSelected: {
                calendarId: undefined,
                grade: undefined,
                major: undefined
            },
            // 通用列表
            commonLists: {
                // 显示在 courseOverview 页面的课程列表
                compulsoryCourses: [], // 必修课
                optionalTypes: [], // 选修课类型
                optionalCourses: [], // 选修课

                // 选择课程时的课程列表
                stagedCourses: [], // 备选课程
                selectedCourses: [], // 已选课程
            },
            // 点击的课程信息
            clickedCourseInfo: {
                courseCode: '',
                courseName: ''
            },
            // 课程表数据
            occupied: Array(12).fill(null).map(() => Array(7).fill(undefined).map(() => [])), // 12 * 7 的二维数组，每个元素是一个数组
            timeTableData: [], // 课程表数据
            // 标志位
            flags: {
                majorNotChanged: false // 专业是否被改变，如果改变了，需要重新向后端请求数据
            }
        }
    },
    mutations: {
        setMajorInfo(state, payload: baseInfoTriplet) {
            state.majorSelected = payload;
            state.flags.majorNotChanged = false;
        },
        setCompulsoryCourses(state, payload: courseInfo[]) {
            state.commonLists.compulsoryCourses = payload;
            state.flags.majorNotChanged = true;
        },
        setOptionalTypes(state, payload) {
            console.log(payload);
            state.commonLists.optionalTypes = payload;
        },
        setOptionalCourses(state, payload) {
            state.commonLists.optionalCourses = payload;
            // console.log(state.commonLists.optionalCourses);
        },
        pushStagedCourse(state, payload) {
            state.commonLists.stagedCourses.push(payload);
            // console.log(state.commonLists.stagedCourses.length);
        },
        popStagedCourse(state, payload) {
            state.commonLists.stagedCourses = state.commonLists.stagedCourses.filter(course => course.courseId !== payload);
        },
        setClickedCourseInfo(state, payload) {
            // console.log(payload);
            state.clickedCourseInfo = payload;
        },
        clearStagednSelectedCourses(state) {
            state.commonLists.stagedCourses = [];
            state.commonLists.selectedCourses = [];
        },
        updateTimeTable(state, payload: courseDetaillet) {      
            // console.log("排课信息:", payload)

            if (canAddCourse(payload.arrangementInfo, state.occupied, payload.code).canAdd) {
                const sameCodeCourse = state.timeTableData?.find(course => isSameCourse(course.code, payload.code));

                // 规定相同课号的课只能有一个
                if (sameCodeCourse) {
                    state.timeTableData = state.timeTableData.filter(course => !isSameCourse(course.code, payload.code));
                    deleteOccupied(state.occupied, sameCodeCourse.occupyTime);
                }

                payload.arrangementInfo.forEach(
                    (arrangement) => {
                        const courseOnTable = { // 每次需要重新创建一个对象，否则会出现引用问题
                            showText: arrangement.teacherAndCode + ' ' + state.clickedCourseInfo.courseName + ' ' + arrangement.arrangementText.split(' ').slice(1).join(' '),
                            courseName: state.clickedCourseInfo.courseName,
                            code: payload.code,
                            occupyTime: arrangement.occupyTime,
                            occupyDay: arrangement.occupyDay,
                        }
                        // console.log("push 了星期", courseOnTable.occupyDay);
                        state.timeTableData.push(courseOnTable);
                    }
                );

                // console.log("当前课表数据：", state.timeTableData);

                insertOccupied(state.occupied, payload.arrangementInfo, payload.code);

            }
            else {
                console.log("课程冲突");
            }

            // console.log(payload);
        }
    },
    getters: {
        isMajorSelected(state) {
            return state.majorSelected.calendarId && state.majorSelected.grade && state.majorSelected.major;
        },
        sortCompulsoryCoursesByGrade(state) {
            // 返回一个数组
            // 每个元素是一个对象，对象的key是年级，value是一个数组，数组中是这个年级的必修课
            // value 按照课程号排序
            // 年级按降序排序
            const sortedCourses = {};
            state.commonLists.compulsoryCourses.forEach(course => {
                if (!sortedCourses[course.grade]) {
                    sortedCourses[course.grade] = [];
                }
                sortedCourses[course.grade].push(course);
            });
            
            for (const key in sortedCourses) {
                sortedCourses[key].sort((a, b) => a.courseId - b.courseId);
            }

            // 把对象转换成数组
            const sortedCoursesArray = [];
            for (const key in sortedCourses) {
                sortedCoursesArray.push({
                    grade: key,
                    courses: sortedCourses[key]
                });
            }

            sortedCoursesArray.sort((a, b) => b.grade - a.grade);

            // console.log(sortedCoursesArray);

            return sortedCoursesArray;
        },
    }
});

export default store;