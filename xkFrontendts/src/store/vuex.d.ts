import { Store } from "vuex";

// 这个文件存在原因是：https://github.com/vuejs/vuex/issues/2213#issuecomment-1592267216
// declare module "vuex" {
//   export * from "vuex/types/index.d.ts";
//   export * from "vuex/types/helpers.d.ts";
//   export * from "vuex/types/logger.d.ts";
//   export * from "vuex/types/vue.d.ts";
// }

declare module 'vue' {
  // 声明自己的 store state
    interface State {
        majorSelected: baseInfoTriplet, /* 持久化 */
        commonLists: {
            compulsoryCourses: courseInfo[],
            optionalTypes: optionalCourseType[],
            optionalCourses: courseInfo[],
            stagedCourses: stagedCourse[], /* 持久化 */
            selectedCourses: string[], /* 持久化 */
            searchCourses: courseInfo[]
        },
        clickedCourseInfo: {
            courseCode: string,
            courseName: string
        },
        occupied: Array<Array<occupyCell[]>>, /* 持久化 */
        timeTableData: courseOnTable[], /* 持久化 */
        flags: {
            majorNotChanged: boolean
        },
        updateTime: string,
        isSpin: boolean
    }

  // 为 `this.$store` 提供类型声明
  interface ComponentCustomProperties {
    $store: Store<State>
  }
}