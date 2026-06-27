<template>
    <a-layout class="space-y-4">
      <MyHeader />
      <MajorInfo @changeMajor="resetSelectedRows" />
        <a-layout>
          <div class="flex flex-row space-x-4 h-max m-2">
            <CourseRoughList @openOverview="handleOpen"/>
            <CourseDetailList />
          </div>
        </a-layout>
        <TimeTable @cellClick="findCourseByTime" />
        <MyFooter />
    </a-layout>
    <a-modal
    title="选择课程"
    okText="提交"
    v-model:open="openOverview"
    @ok="stageCourses"
    @cancel="handleCancel"
    style="width: 80%"
      >
      <CourseOverview v-model:selectedRowKeys="selectedRowKeys" />
    </a-modal>

    <a-modal
      title="选修课"
      okText="提交"
      v-model:open="openOptional"
      @ok="stageCourses"
      @cancel="handleCancel"
      style="width: 80%"
    >
      <OptionalCourseTimeOverview v-model:selectedRowKeys="selectedRowKeys" v-model:optionalCourseData="optionalCourseData" />
    </a-modal>
</template>

<script lang="ts">
import axios from 'axios';
import { defineAsyncComponent } from 'vue';
import { errorNotify } from '../utils/notify';
import { getRowSection } from '../utils/timetable';
import type { courseInfo } from '../utils/myInterface';

export default {
  name: 'CourseScheduler',
  components: {
    MyHeader: defineAsyncComponent(() => import('../components/MyHeader.vue')),
    MyFooter: defineAsyncComponent(() => import('../components/MyFooter.vue')),
    CourseRoughList: defineAsyncComponent(() => import('../components/CourseRoughList.vue')),
    CourseDetailList: defineAsyncComponent(() => import('../components/CourseDetailList.vue')),
    TimeTable: defineAsyncComponent(() => import('../components/TimeTable.vue')),
    MajorInfo: defineAsyncComponent(() => import('../components/MajorInfo.vue')),
    CourseOverview: defineAsyncComponent(() => import('../components/CourseOverview.vue')),
    OptionalCourseTimeOverview: defineAsyncComponent(() => import('../components/OptionalCourseTimeOverview.vue'))
  },
  data() {
    return {
      selectedRowKeys: [] as string[],
      openOverview: false,
      openOptional: false,
      optionalCourseData: []
    }
  },
  methods: {
    handleOpen() {
      this.openOverview = true;
      // console.log("openOverview", this.openOverview);
    },
    handleCancel() {
      this.openOverview = false;
      this.selectedRowKeys = []; // 清空一下，不然动画会保持原来的状态
      // console.log("清空！", this.selectedRowKeys);
    },
    handleCancelOptional() {
      this.openOptional = false;
      this.selectedRowKeys = [];
    },
    resetSelectedRows() {
      // console.log("resetSelectedRows");
      this.selectedRowKeys = [];
    },
    async stageCourses() {
      this.openOverview = false;
      this.openOptional = false;
      this.$store.commit("setSpin", true);
      
      // 收集所有需要请求课程详情的课程代码
      const optionalCodes: string[] = [];
      const searchCodes: string[] = [];
      const compulsoryCourses: string[] = [];

      // 第一步：分类所有选中的课程
      for (const key of this.selectedRowKeys) {
        const type = key[0];

        if (type === '必') {
          compulsoryCourses.push(key);
        }
        else if (type === '选') {
          const _courseCode = key.split('_')[2];
          optionalCodes.push(_courseCode);
        }
        else if (type === '查') {
          const _courseCode = key.split('_')[1];
          searchCodes.push(_courseCode);
        }
      }

      // 第二步：处理必修课（直接从 vuex 获取）
      for (const key of compulsoryCourses) {
        const _courseCode = key.split('_')[2];
        const originalCourse = this.$store.state.commonLists.compulsoryCourses.find((course: courseInfo) => course.courseCode === _courseCode);
        
        const _courseObject = {
          courseCode: originalCourse.courseCode,
          courseName: originalCourse.courseName + '(' + originalCourse.courseCode + ')',
          courseNameReserved: originalCourse.courseName,
          credit: originalCourse.credit,
          courseType: "必",
          teacher: [],
          status: 0,
          courseDetail: originalCourse.courses.map((course: Record<string, unknown>) => ({
            ...course,
            status: 0
          }))
        }

        this.$store.commit("pushStagedCourse", _courseObject);
      }

      // 第三步：批量请求选修课详情
      if (optionalCodes.length > 0) {
        try {
          const res = await axios({
            url: '/api/findCourseDetailByCode',
            method: 'post',
            data: {
              courseCodes: optionalCodes,
              calendarId: this.$store.state.majorSelected.calendarId
            }
          });

          const courseDetailMap = res.data.data; // { courseCode: [details] }

          for (const courseCode of optionalCodes) {
            try {
              // 优先从 optionalCourses 查找，如果找不到则从 optionalCourseData 查找
              let _roughCourse = this.$store.state.commonLists.optionalCourses
                .find((courseGroup: { courses: Array<{ courseCode: string }> }) => courseGroup.courses.some((course: { courseCode: string }) => course.courseCode === courseCode))
                ?.courses.find((course: { courseCode: string }) => course.courseCode === courseCode);
              
              if (!_roughCourse) {
                _roughCourse = this.optionalCourseData.find((course: { courseCode: string }) => course.courseCode === courseCode);
              }
              
              if (!_roughCourse) {
                throw new Error(`找不到课程 ${courseCode} 的基本信息`);
              }
              
              const _detailCourse = courseDetailMap[courseCode] || [];

              const _courseObject = {
                courseCode: _roughCourse.courseCode,
                courseName: _roughCourse.courseName + '(' + _roughCourse.courseCode + ')',
                courseNameReserved: _roughCourse.courseName,
                credit: _roughCourse.credit,
                courseType: "选",
                teacher: [],
                status: 0,
                courseDetail: _detailCourse.map((course: Record<string, unknown>) => ({
                  ...course,
                  status: 0
                }))
              }

              this.$store.commit("pushStagedCourse", _courseObject);
            }
            catch (error: unknown) {
              const err = error as Error;
              errorNotify(err.message || `添加课程 ${courseCode} 失败`);
            }
          }
        }
        catch (error: unknown) {
          const err = error as { response?: { data?: { msg?: string } }; message?: string };
          errorNotify(err.response?.data?.msg || err.message || '批量添加选修课失败');
        }
      }

      // 第四步：批量请求搜索课程详情
      if (searchCodes.length > 0) {
        try {
          const res = await axios({
            url: '/api/findCourseDetailByCode',
            method: 'post',
            data: {
              courseCodes: searchCodes,
              calendarId: this.$store.state.majorSelected.calendarId
            }
          });

          const courseDetailMap = res.data.data;

          for (const courseCode of searchCodes) {
            try {
              const _roughCourse = this.$store.state.commonLists.searchCourses
                .find((course: courseInfo) => course.courseCode === courseCode);
              
              if (!_roughCourse) {
                throw new Error(`找不到课程 ${courseCode} 的基本信息`);
              }

              const _detailCourse = courseDetailMap[courseCode] || [];

              const _courseObject = {
                courseCode: _roughCourse.courseCode,
                courseName: _roughCourse.courseName + '(' + _roughCourse.courseCode + ')',
                courseNameReserved: _roughCourse.courseName,
                credit: _roughCourse.credit,
                courseType: "查",
                teacher: [],
                status: 0,
                courseDetail: _detailCourse.map((course: Record<string, unknown>) => ({
                  ...course,
                  status: 0
                }))
              }

              this.$store.commit("pushStagedCourse", _courseObject);
            }
            catch (error: unknown) {
              const err = error as Error;
              errorNotify(err.message || `添加课程 ${courseCode} 失败`);
            }
          }
        }
        catch (error: unknown) {
          const err = error as { response?: { data?: { msg?: string } }; message?: string };
          errorNotify(err.response?.data?.msg || err.message || '批量添加搜索课程失败');
        }
      }

      // 清空 selectedRowKeys
      this.selectedRowKeys = [];
      this.$store.commit("setSpin", false);
    },
    async findCourseByTime(cell: { day: number; class: number; calendarId: number }) {
      this.$store.commit("setSpin", true);
      console.log("cell", cell);

      try {
        const res = await axios({
          url: '/api/findCourseByTime',
          method: 'post',
          data: {
            calendarId: cell.calendarId,
            day: cell.day,
            section: getRowSection(cell.class, cell.calendarId)
          }
        });

        // console.log("res", res.data.data);

        this.optionalCourseData = res.data.data;
        this.openOptional = true;
      }
      catch (error: unknown) {
        // console.log("error:", error);
        const err = error as { response?: { data?: { msg?: string } } };
        errorNotify(err.response?.data?.msg || '查询课程失败');
      }
      finally {
        this.$store.commit("setSpin", false);
      }
    }
  }
}
</script>
