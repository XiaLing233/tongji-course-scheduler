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
                        <a-button type="primary">
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
                    :custom-row="onRowClick"
                >
                    <template #bodyCell="{ column, record }">
                        <template v-if="column.key === 'status'">
                            <a-tag :color="record.status === '已选' ? 'success' : (record.status === '备选' ? 'warning' : 'error')">
                                {{ record.status }}
                            </a-tag>
                        </template>
                        <template v-else-if="column.key === 'action'">
                            <span>foo</span>
                        </template>
                    </template>
                </a-table>
            </a-card>
        </div>    
    </a-layout-content>
</template>

<script>
import axios from 'axios';

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
                dataIndex: 'teacherName',
                key: 'teacherName',
                align: 'center'
            },
            {
                title: '状态',
                dataIndex: 'status',
                key: 'status',
                align: 'center'
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
                console.log("未选择专业");
                return;
            }
            // 如果专业没变，不重新获取
            if (this.$store.state.flags.majorNotChanged) {
                console.log("专业未变");
                this.$emit('openOverview');
                return;
            }
            // 获取必修课程
            try {
                const res = await axios({
                url: '/api/findCourseByMajor',
                method: 'post',
                data: {
                    grade: this.$store.state.majorSelected.grade,
                    code: this.$store.state.majorSelected.major,
                    calendarId: this.$store.state.majorSelected.calendar
                }
            })
            this.$store.commit('setCompulsoryCourses', res.data.data);
            this.$emit('openOverview');
            }
            catch (error) {
                console.log("error:", error);
            }
        },
        getRowClass(_record, index) {
            // console.log(index);
            return index % 2 === 0 ? 'bg-white' : 'bg-gray-50'
        },
        onRowClick(record, _index) {
            return {
                onClick: () => {
                    // console.log(record)
                    this.$store.commit('setClickedCourseInfo', {
                        courseCode: record.courseCode,
                        courseName: record.courseNameReserved
                    });
                }
            }
        }
    },
    emits: ['openOverview'],
}
</script>