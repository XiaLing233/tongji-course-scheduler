<template>
    <a-layout-content class="w-[60%]">
        <a-card
            :title="title"
        >
            <a-table
                :columns="columns"
                :data-source="localDetailList"
                :pagination="false"
                :row-class-name="getRowClass"
                class="h-80 overflow-auto"
                :custom-row="onRowEvent"
                bordered
            >
                <template #bodyCell="{ column, record }">
                    <template v-if="column.key === 'campus'">
                        <div :class="getCampusClass(record.campus)" class="h-full flex items-center justify-center">
                            <p>{{ record.campus }}</p>
                        </div>
                    </template>
                    <template v-else-if="column.key === 'status'">
                        <span :class="getStatusTextColor(record.status)">
                            {{ mapStatusToChinese(record.status) }}
                        </span>
                    </template>
                    <template v-else-if="column.key === 'code'">
                        <div class="flex flex-row items-center justify-center">
                            <a-tag color="green" v-if="record.isExclusive">专业课表</a-tag>
                            <p>{{ record.code }}</p>
                        </div>
                    </template>
                </template>
            </a-table>
        </a-card>
    </a-layout-content>
</template>

<script>
import { mapStatusToChinese } from '@/utils/statusManipulate';

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
                        align: 'center',
                        customCell: () => ({
                            style: {
                            padding: '0',
                            height: '4px' // 几 px 都无所谓，没效果的..但是得有，不然占不满整个单元格
                            }
                        })
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
                        align: 'center',
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
                // console.log(this.$store.state.commonLists.stagedCourses.find(course => course.courseCode === this.$store.state.clickedCourseInfo.courseCode)?.courseDetail)
                return this.$store.state.commonLists.stagedCourses.find(course => course.courseCode === this.$store.state.clickedCourseInfo.courseCode)?.courseDetail || [];
            },
            title() {
                const courseInfo = this.$store.state.clickedCourseInfo;
                // console.log("courseInfo", courseInfo);
                return `${courseInfo.courseName} ${courseInfo.courseCode}`;
            }
        },
        methods: {
            getCampusClass(campus) {
                switch (campus) {
                    case '四平路校区':
                        return 'bg-yellow-100/80';
                    case '嘉定校区':
                        return 'bg-red-100/80';
                    case '沪西校区':
                        return 'bg-white';
                    default:
                        return 'bg-white';
                }
            },
            onRowEvent(courseDetaillet) {
                return {
                    onClick: () => {
                        // console.log("记录", courseDetaillet);
                        this.$store.commit('updateTimeTable', courseDetaillet);
                    }
                }
            },
            mapStatusToChinese,
            getStatusTextColor(status) {
                // console.log("132", status);
                switch (status) {
                    case 0:
                        return '';
                    case 1:
                        return 'text-yellow-300';
                    case 2:
                        return 'text-red-500';
                    default:
                        return '';
                }
            },
            getRowClass(record, index) {
                let className = index % 2 === 0 ? 'bg-white' : 'bg-gray-50';
                
                switch (record.status) {
                    case 0: // 未选
                        break;
                    case 1: // 备选
                        className =  'bg-blue-500/60';
                        break;
                    case 2:
                        className += ' ' + 'text-red-500';
                        break;
                    default:
                        break;
                }

                // console.log("className", className);

                return className;
            }
        }
    }
</script>

<style scoped>
:deep(.ant-table-tbody > tr.ant-table-row:hover > td),
:deep(.ant-table-tbody > tr > td.ant-table-cell-row-hover) {
  background: transparent !important;
}
</style>