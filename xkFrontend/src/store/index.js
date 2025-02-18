import { createStore } from "vuex";

const store = createStore({
    state() {
        return {
            majorSelected: {
                calendar: undefined,
                grade: undefined,
                major: undefined
            },
            commonLists: {
                compulsoryCourses: [],
                optionalTypes: [],
                optionalCourses: [],
            },
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
            console.log(state.commonLists.optionalCourses);
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

            console.log(sortedCoursesArray);

            return sortedCoursesArray;
        },
        getRoughCourses(state) {
            return [];
        }
    }
});

export default store;