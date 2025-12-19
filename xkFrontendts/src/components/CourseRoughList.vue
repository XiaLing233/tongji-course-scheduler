<template>
    <a-layout-content class="h-[40%]">
        <div>
            <a-card
                title="选课列表"
            >
                <template #extra>
                    <div class="flex flex-row space-x-4 items-center">
                        <a-button @click="getCompulsoryCourses">
                            <p>选择课程</p>
                        </a-button>
                        <a-button type="primary" @click="handleSave">
                            <p>保存课表</p>
                        </a-button>
                    </div>
                </template>
                <a-table
                    :columns="columns"
                    :data-source="$store.state.commonLists.stagedCourses"
                    :pagination="false"
                    :row-class-name="getRowClass"
                    class="h-80 overflow-auto"
                    bordered
                    :custom-row="onRowEvent"
                    :rowHoverable="false"
                >
                    <template #bodyCell="{ column, record }">
                        <template v-if="column.key === 'status'">
                            <span :class="getStatusTextColor(record.status)">
                                {{ mapStatusToChinese(record.status) }}
                            </span>
                        </template>
                        <template v-else-if="column.key === 'action'">
                            <!-- .stop 是为了事件不冒泡 -->
                            <a-button type="link" @click.stop="$store.commit('popStagedCourse', record.courseCode)">
                                <div class=" text-red-500">
                                    <span v-if="record.status === 2" >退课</span>
                                    <span v-else>清除</span>
                                </div>
                            </a-button>
                        </template>
                    </template>
                </a-table>
            </a-card>
        </div>    
    </a-layout-content>
</template>

<script lang="ts">
import axios from 'axios';
import { mapStatusToChinese } from '@/utils/statusManipulate';
import { errorNotify } from '@/utils/notify';
import type { teacherlet, courseInfo } from '@/utils/myInterface';

export default {
    data() {
        return {
            columns: [
            {
                title: '课程名称',
                dataIndex: 'courseName',
                key: 'courseName',
                align: 'center'
            },
            {
                title: '学分',
                dataIndex: 'credit',
                key: 'credit',
                align: 'center'
            },
            {
                title: '必/选',
                dataIndex: 'courseType',
                key: 'courseType',
                align: 'center'
            },
            {
                title: '教师',
                dataIndex: 'teacher',
                key: 'teacher',
                align: 'center',
                customRender: ({ text }: { text: teacherlet[] }) => text?.map(teacher => teacher.teacherName).join(', ')
            },
            {
                title: '状态',
                dataIndex: 'status',
                key: 'status',
                align: 'center',
            },
            {
                title: '操作',
                key: 'action',
                align: 'center'
            }
        ],
        }
    },
    methods: {
        async getCompulsoryCourses() {
            // 如果没选择专业
            if (!this.$store.getters.isMajorSelected) {
                // console.log("未选择专业");
                errorNotify("未选择专业");
                return;
            }
            // 如果专业没变，不重新获取
            if (this.$store.state.flags.majorNotChanged) {
                // console.log("专业未变");
                this.$emit('openOverview');
                return;
            }

            this.$store.commit('setSpin', true);

            // 获取必修课程
            try {
                const res = await axios({
                url: '/api/findCourseByMajor',
                method: 'post',
                data: {
                    grade: this.$store.state.majorSelected.grade,
                    code: this.$store.state.majorSelected.major,
                    calendarId: this.$store.state.majorSelected.calendarId
                }
            })
            this.$store.commit('setCompulsoryCourses', res.data.data);
            this.$emit('openOverview');
            }
            catch (error: any) {
                // console.log("error:", error);
                errorNotify(error.response.data.msg);
            }
            finally {
                this.$store.commit('setSpin', false);
            }
        },
        getRowClass(record: any, index: number) {
            // console.log(index);
            let className = index % 2 === 0 ? 'bg-white' : 'bg-gray-50';

            if (record.courseCode === this.$store.state.clickedCourseInfo.courseCode) {
                className = 'bg-blue-400/60';
            }

            return className;
        },
        onRowEvent(record: courseInfo) {
            return {
                onClick: () => {
                    // console.log(record)
                    this.$store.commit('setClickedCourseInfo', {
                        courseCode: record.courseCode,
                        courseName: record.courseNameReserved
                    });
                },
            }
        },
        mapStatusToChinese,
        getStatusTextColor(status: number) {
            switch(status) {
                case 0:
                    return '';
                case 1:
                    return 'text-yellow-300';
                case 2:
                    return 'text-green-400';
                default:
                    return '';
            }
        },
        handleSave() {
            this.$store.commit('saveSelectedCourses');
            this.$store.commit('solidify');
        }
    },
    emits: ['openOverview'],
}
</script>

<style scoped>
:deep(.ant-table-tbody > tr.ant-table-row:hover > td),
:deep(.ant-table-tbody > tr > td.ant-table-cell-row-hover) {
  background: transparent !important;
}
</style>