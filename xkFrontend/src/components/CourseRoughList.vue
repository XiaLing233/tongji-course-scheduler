<template>
    <a-layout-content>
        <a-card
            title="选课列表"
        >
            <template #extra>
                <div class="flex flex-row space-x-4 items-center">
                    <a-button>
                        <p>选择课程</p>
                    </a-button>
                    <a-button type="primary">
                        <p>保存课表</p>
                    </a-button>
                </div>
            </template>
            <a-table
                :columns="columns"
                :data-source="roughCourses"
                :row-class-name="(_record, index) => (index % 2 === 1 ? 'table-striped' : null)"
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
                    title: '课程名称',
                    dataIndex: 'courseName',
                    scopedSlots: { customRender: 'courseName' },
                    align: 'center'
                },
                {
                    title: '学分',
                    dataIndex: 'credit',
                    scopedSlots: { customRender: 'credit' },
                    align: 'center'
                },
                {
                    title: '教师',
                    dataIndex: 'teacherName',
                    scopedSlots: { customRender: 'teacherName' },
                    align: 'center'
                },
                {
                    title: '状态',
                    dataIndex: 'status',
                    scopedSlots: { customRender: 'status' },
                    align: 'center'
                },
                {
                    title: '操作',
                    key: 'action',
                    scopedSlots: { customRender: 'action' },
                    align: 'center'
                }
            ],
                roughCourses: []
            }
        }
    }
</script>