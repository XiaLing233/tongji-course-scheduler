<template>
    <div class="overflow-auto h-150">
        <a-table
            :columns="columns"
            :data-source="filteredCourses(optionalCourseData)"
            :pagination="false"
            :row-selection="{ 
                selectedRowKeys: localSelectedRowKeys,
                onChange: (keys) => onOptionalSelectChange(keys) 
            }"
            :row-key="record => '选_' + record.courseNature + '_' + record.courseCode"
            :row-class-name="(_record, index) => index % 2 === 1 ? 'bg-gray-50' : ''"
        >
        </a-table>
    </div>
</template>

<script>
export default {
    data() {
        return {
            columns: [
                {
                    title: '课程代码',
                    dataIndex: 'courseCode',
                    align: 'center'
                },
                {
                    title: '课程名称',
                    dataIndex: 'courseName',
                    align: 'center'
                },
                {
                    title: '开课学院',
                    dataIndex: 'faculty',
                    align: 'center'
                },
                {
                    title: '学分',
                    dataIndex: 'credit',
                    align: 'center'
                },
                {
                    title: '课程性质',
                    dataIndex: 'courseNature',
                    key: 'courseNature',
                    align: 'center',
                    customRender: ({ text }) => text ? text.join('、') : ''
                },
                {
                    title: '校区',
                    dataIndex: 'campus',
                    align: 'center',
                    customRender: ({ text }) => text ? text.join('、') : ''
                }
            ],
        }
    },
    methods: {
        filteredCourses(courses) {
            return courses.filter((course) => {
                return !this.$store.state.commonLists.stagedCourses.some(stagedCourse => stagedCourse.courseCode === course.courseCode);
            });
        },
        onOptionalSelectChange(keys) {
            this.localSelectedRowKeys = keys;
        }
    },
    computed: {
        localSelectedRowKeys: {
            get() {
                // console.log('localSelectedRowKeys', this.selectedRowKeys);
                return this.selectedRowKeys;
            },
            set(value) {
                this.$emit('update:selectedRowKeys', value);
            }
        }
    },
    props: ['selectedRowKeys', 'optionalCourseData'],
}
</script>