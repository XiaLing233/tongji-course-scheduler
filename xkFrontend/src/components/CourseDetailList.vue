<template>
    <a-layout-content class="w-[60%]">
        <a-card
            :title="title"
        >
            <a-table
                :columns="columns"
                :data-source="localDetailList"
                :pagination="false"
                :row-class-name="(_record, index) => (index % 2 === 1 ? 'table-striped' : null)"
                class="h-80 overflow-auto"
                bordered
            >
            </a-table>
        </a-card>
    </a-layout-content>
</template>

<script>
    export default {
        data() {
            return {
                columns: [
                    {
                        title: '课程序号',
                        dataIndex: 'code',
                        key: 'code',
                        align: 'center',
                        sorter: (a, b) => a.code - b.code
                    },
                    {
                        title: '教师',
                        dataIndex: 'teachers',
                        key: 'teachers',
                        align: 'center',
                        customRender: ({ text }) => text?.map(teacher => teacher.teacherName).join(', ')
                    },
                    {
                        title: '校区',
                        dataIndex: 'campus',
                        key: 'campus',
                        align: 'center'
                    },
                    {
                        title: '课程安排',
                        dataIndex: 'arrangementInfo',
                        key: 'arrangementInfo',
                        align: 'center',
                        customRender: ({ text }) => text?.map(arrangement => arrangement.arrangementText).join(', ')
                    },
                    {
                        title: '状态',
                        dataIndex: 'status',
                        key: 'status',
                        align: 'center'
                    },
                    {
                        title: '语言',
                        dataIndex: 'teachingLanguage',
                        key: 'language',
                        align: 'center'
                    }
                ],
            }
        },
        computed: {
            localDetailList() {
                console.log(this.$store.state.commonLists.stagedCourses.find(course => course.courseCode === this.$store.state.clickedCourseInfo.courseCode)?.courseDetail)
                return this.$store.state.commonLists.stagedCourses.find(course => course.courseCode === this.$store.state.clickedCourseInfo.courseCode)?.courseDetail || []
            },
            title() {
                const courseInfo = this.$store.state.clickedCourseInfo;
                return `${courseInfo.courseName} ${courseInfo.courseCode}`
            }
        },
    }
</script>