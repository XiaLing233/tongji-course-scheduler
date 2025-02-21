<template>
  <a-config-provider :locale="locale">
    <a-layout class="space-y-4">
      <!-- 所有 layout 放在了组件里, 不要嵌套! -->
      <MyHeader />
      <MajorInfo @changeMajor="resetSelectedRows" />
      <a-layout>
        <div class="flex flex-row space-x-4 h-max m-2">
          <CourseRoughList @openOverview="handleOpen"/>
          <CourseDetailList />
        </div>
      </a-layout>
      <TimeTable />
    </a-layout>
    <a-modal
    title="选择课程"
    okText="提交"
    v-model:open="openOverview"
    @ok="stageCourses"
    @cancel="openOverview = false"
    style="width: 80%"
      >
      <CourseOverview v-model:selectedRowKeys="selectedRowKeys" />
    </a-modal>
  </a-config-provider>
</template>

<script>
import MyHeader from './components/MyHeader.vue';
import CourseRoughList from './components/CourseRoughList.vue';
import CourseDetailList from './components/CourseDetailList.vue';
import TimeTable from './components/TimeTable.vue';
import MajorInfo from './components/MajorInfo.vue';
import CourseOverview from './components/CourseOverview.vue';

import zhCN from 'ant-design-vue/es/locale/zh_CN';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';
import axios from 'axios';


dayjs.locale('zh-cn');

export default {
  name: 'App',
  components: {
    MyHeader,
    CourseRoughList,
    CourseDetailList,
    TimeTable,
    MajorInfo,
    CourseOverview
  },
  data() {
    return {
      locale: zhCN,
      selectedRowKeys: [],
      openOverview: false
    }
  },
  methods: {
    handleOpen() {
      this.openOverview = true;
      // console.log("openOverview", this.openOverview);
    },
    resetSelectedRows() {
      // console.log("resetSelectedRows");
      this.selectedRowKeys = [];
    },
    async stageCourses() {
      this.openOverview = false;
      
      // 根据 selectedRowKeys 筛选出对应的课程信息
      for (const key of this.selectedRowKeys) {
        // 根据第一个字符分类
        const type = key[0];

        if (type === '必') {
          // 如果是必修课，则直接在 vuex 的状态里查找
          const _courseCode = key.split('_')[2];

          // 整合一下
          const originalCourse = this.$store.state.commonLists.compulsoryCourses.find(course => course.courseCode === _courseCode);
          
          const _courseObject = {
            courseCode: originalCourse.courseCode,
            courseName: originalCourse.courseName + '(' + originalCourse.courseCode + ')',
            courseNameReserved: originalCourse.courseName,
            credit: originalCourse.credit,
            courseType: "必",
            teacher: [],
            status: 0,
            courseDetail: originalCourse.courses.map(course => ({
              ...course,
              status: 0
            }))
          }


          this.$store.commit("pushStagedCourse", _courseObject);
        }
        else if (type === '选') {
          // 如果是选修课，需要向后端请求
          // console.log('选修课', key);

          const _courseCode = key.split('_')[2];

          try {
            const res = await axios({
              url: '/api/findCourseDetailByCode',
              method: 'post',
              data: {
                courseCode: _courseCode,
                calendarId: this.$store.state.majorSelected.calendarId
              }
            });

            // 需要整合一下数据
            // 思路：先找到包含这个课程的选修课类别，然后再在这个类别中定位到这个课程
            const _roughCourse = this.$store.state.commonLists.optionalCourses
              .find(courseGroup => courseGroup.courses.some(course => course.courseCode === _courseCode))
              ?.courses.find(course => course.courseCode === _courseCode);
            const _detailCourse = res.data.data;

            const _courseObject = {
              courseCode: _roughCourse.courseCode,
              courseName: _roughCourse.courseName + '(' + _roughCourse.courseCode + ')',
              courseNameReserved: _roughCourse.courseName,
              credit: _roughCourse.credit,
              courseType: "选",
              teacher: [],
              status: 0,
              courseDetail: _detailCourse.map(course => ({
                ...course,
                status: 0
              }))
            }

            // console.log("_courseObject", _courseObject);

            this.$store.commit("pushStagedCourse", _courseObject);
          }
          catch (error) {
            console.log("error:", error);
          }
        }
      }

      // 清空 selectedRowKeys
      this.selectedRowKeys = [];
    }
  }
}
</script>