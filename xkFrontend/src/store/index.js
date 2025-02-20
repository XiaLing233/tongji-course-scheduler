import { createStore } from "vuex";

const store = createStore({
    state() {
        return {
            // 检索的基本信息
            majorSelected: {
                calendar: undefined,
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
            clickedCourseInfo: {
                courseCode: '',
                courseName: ''
            },
            // 标志位
            flags: {
                majorNotChanged: false // 专业是否被改变，如果改变了，需要重新向后端请求数据
            }
        }
    },
    mutations: {
        setMajorInfo(state, payload) {
            state.majorSelected = payload;
            state.flags.majorNotChanged = false;
        },
        setCompulsoryCourses(state, payload) {
            state.commonLists.compulsoryCourses = payload;
            state.flags.majorNotChanged = true;
        },
        setOptionalTypes(state, payload) {
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
        }
    },
    getters: {
        isMajorSelected(state) {
            return state.majorSelected.calendar && state.majorSelected.grade && state.majorSelected.major;
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