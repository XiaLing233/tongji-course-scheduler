<template>
  <a-config-provider :locale="locale">
    <a-layout class="space-y-4">
      <!-- 所有 layout 放在了组件里, 不要嵌套! -->
      <Header />
      <MajorInfo />
      <a-layout>
        <div class="flex flex-row space-x-4 h-max m-2">
          <CourseRoughList @openOverview="handleOpen"/>
          <CourseDetailList title="test123" />
        </div>
      </a-layout>
      <TimeTable :timeTableData="timeTableData" />
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
import Header from './components/Header.vue';
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
    Header,
    CourseRoughList,
    CourseDetailList,
    TimeTable,
    MajorInfo,
    CourseOverview
  },
  data() {
    return {
      locale: zhCN,
      timeTableData: [
          {
            "courseName": "人工智能课程设计",
            "code": "10057902",
            "teacherName": "武妍",
            "teacherCode": "92724",
            "arrangementText": "[1-17] 学院教室",
            "occupyTime": [1,2],
            "occupyDay": 2
          },
          {
            "courseName": "计算机组成原理课程设计",
            "code": "10065604",
            "teacherName": "张冬冬",
            "teacherCode": "09049",
            "arrangementText": "[1-17] 学院教室",
            "occupyTime": [1,2],
            "occupyDay": 3
          },
          {
            "courseName": "数据库系统原理",
            "code": "10039602",
            "teacherName": "李文根",
            "teacherCode": "19034",
            "arrangementText": "[1-17] 广楼G107",
            "occupyTime": [3,4],
            "occupyDay": 1
          },
          {
            "courseName": "人工智能原理与技术",
            "code": "10058002",
            "teacherName": "武妍",
            "teacherCode": "92724",
            "arrangementText": "[1-17] 博楼B213",
            "occupyTime": [3,4],
            "occupyDay": 2
          },
          {
            "courseName": "数据库系统原理",
            "code": "10039602",
            "teacherName": "李文根",
            "teacherCode": "19034",
            "arrangementText": "[1-17单] 广楼G107",
            "occupyTime": [3,4],
            "occupyDay": 3
          },
          {
            "courseName": "数据结构与算法设计2",
            "code": "10066501",
            "teacherName": "张亚英",
            "teacherCode": "05152",
            "arrangementText": "[2-16双] 博楼B414",
            "occupyTime": [3,4],
            "occupyDay": 3
          },
          {
            "courseName": "体育(4)",
            "code": "320004C3",
            "teacherName": "于正直",
            "teacherCode": "21138",
            "arrangementText": "[1-17] 第1-4周体育中心二楼，5-17同舟河",
            "occupyTime": [3,4],
            "occupyDay": 4
          },
          {
            "courseName": "数据结构与算法设计2",
            "code": "10066501",
            "teacherName": "张亚英",
            "teacherCode": "05152",
            "arrangementText": "[1-17] 博楼B414",
            "occupyTime": [3,4],
            "occupyDay": 5
          },
          {
            "courseName": "马克思主义基本原理",
            "code": "54011114",
            "teacherName": "陈红睿",
            "teacherCode": "19052",
            "arrangementText": "[1-17] 博楼B112",
            "occupyTime": [5,6,7],
            "occupyDay": 1
          },
          {
            "courseName": "形势与政策(4)",
            "code": "54010230",
            "teacherName": "林秋琴",
            "teacherCode": "08055",
            "arrangementText": "[7-10] 广楼G204",
            "occupyTime": [5,6],
            "occupyDay": 2
          },
          {
            "courseName": "计算机组成原理",
            "code": "10061204",
            "teacherName": "张冬冬",
            "teacherCode": "09049",
            "arrangementText": "[1-17] 安楼A408",
            "occupyTime": [5,6,7],
            "occupyDay": 3
          },
          {
            "courseName": "拓扑学",
            "code": "5000244006401",
            "teacherName": "周羚君",
            "teacherCode": "06078",
            "arrangementText": "[1-17] 学院教室",
            "occupyTime": [10,11],
            "occupyDay": 3
          }
        ],
      selectedRowKeys: [],
      openOverview: false
    }
  },
  methods: {
    handleOpen() {
      this.openOverview = true;
      // console.log("openOverview", this.openOverview);
    },
    async stageCourses() {
      this.openOverview = false;
      
      // 根据 selectedRowKeys 筛选出对应的课程信息
      for (let key of this.selectedRowKeys) {
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
            credit: originalCourse.credit,
            courseType: "必",
            teacher: [],
            status: "未选",
            courseDetail: originalCourse.courses
          }


          this.$store.commit("pushStagedCourse", _courseObject);
        }
        else if (type === '选') {
          // 如果是选修课，需要向后端请求
          console.log('选修课', key);

          const _courseCode = key.split('_')[2];

          try {
            const res = await axios({
              url: '/api/findCourseDetailByCode',
              method: 'post',
              data: {
                courseCode: _courseCode,
                calendarId: this.$store.state.majorSelected.calendar
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
              credit: _roughCourse.credit,
              courseType: "选",
              teacher: [],
              status: "未选",
              courseDetail: _detailCourse
            }

            console.log("_courseObject", _courseObject);

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