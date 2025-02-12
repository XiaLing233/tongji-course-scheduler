<template>
  <a-config-provider :locale="locale">
    <a-layout>
      <!-- 所有 layout 放在了组件里, 不要嵌套! -->
      <Header />
      <a-layout>
        <CourseList />
      </a-layout>
      <a-layout-content>
        <TimeTable :timeTableData="timeTableData" />
      </a-layout-content>
    </a-layout>
  </a-config-provider>
</template>

<script>
import Header from './components/Header.vue';
import CourseList from './components/CourseList.vue';
import TimeTable from './components/TimeTable.vue';

import zhCN from 'ant-design-vue/es/locale/zh_CN';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';

dayjs.locale('zh-cn');

export default {
  name: 'App',
  components: {
    Header,
    CourseList,
    TimeTable,
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
        ]

    }
  },
}
</script>