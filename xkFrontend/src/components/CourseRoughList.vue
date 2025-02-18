<template>
    <a-layout-content>
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
                :data-source="this.$store.getters.getRoughCourses"
                :row-class-name="(_record, index) => (index % 2 === 1 ? 'table-striped' : null)"
            >
            </a-table>
        </a-card>
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
                align: 'center'
            },
            {
                title: '学分',
                dataIndex: 'credit',
                align: 'center'
            },
            {
                title: '教师',
                dataIndex: 'teacherName',
                align: 'center'
            },
            {
                title: '状态',
                dataIndex: 'status',
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
        }
    },
    emits: ['openOverview'],
}
</script>