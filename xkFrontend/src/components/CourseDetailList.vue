<template>
    <a-layout-content>
        <a-card
            :title="title"
        >
            <a-table
                :columns="columns"
                :data-source="roughCourses"
                :row-class-name="(_record, index) => (index % 2 === 1 ? 'table-striped' : null)"
                class="h-80 overflow-auto"
            >
            </a-table>
        </a-card>
    </a-layout-content>
</template>

<script>
    export default {
        props: {
            title: {
                type: String,
                required: true
            }
        },
        data() {
            return {
                columns: [
                    {
                        title: '课程序号',
                        dataIndex: 'code',
                        key: 'code',
                        align: 'center'
                    },
                    {
                        title: '教师',
                        dataIndex: 'teacherName',
                        key: 'teacherName',
                        align: 'center'
                    },
                    {
                        title: '校区',
                        dataIndex: 'campus',
                        key: 'campus',
                        align: 'center'
                    },
                    {
                        title: '课程安排',
                        dataIndex: 'arrangementText',
                        key: 'arrangementText',
                        align: 'center'
                    },
                    {
                        title: '状态',
                        dataIndex: 'status',
                        key: 'status',
                        align: 'center'
                    },
                    {
                        title: '语言',
                        dataIndex: 'teachingLanguageI18n',
                        key: 'language',
                        align: 'center'
                    }
                ],
            }
        }
    }
</script>