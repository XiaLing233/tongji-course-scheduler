<template>
    <div
        class="flex flex-col w-full"
    >
        <div>
            <a-radio-group v-model:value="selectedType">
                <a-radio-button value="compulsory">计划内课程</a-radio-button>
                <a-radio-button value="optional">通识选修课</a-radio-button>
                <a-radio-button value="search">高级检索</a-radio-button>
            </a-radio-group>
        </div>
        <div v-if="selectedType === 'compulsory'">
            <div class="h-150 overflow-auto">
                <a-table
                :columns="columns.compulsory"
                v-for="courses in this.$store.getters.sortCompulsoryCoursesByGrade"
                :data-source="courses.courses"
                :pagination="false"
                :title="() => courses.grade + '级'"
                :row-selection="{ 
                    selectedRowKeys: selectedRowKeys.filter(key => key.startsWith(courses.grade + '_')), 
                    onChange: (keys) => onSelectChange(keys, courses.grade) 
                }"
                :row-key="record => courses.grade + '_' + record.courseCode"
            >
            </a-table>
            </div>
        </div>
        <div v-else-if="selectedType === 'optional'">
            <a-tabs v-model:activeKey="selectedOptionalType">
                <a-tab-pane v-for="type in $store.state.commonLists.optionalTypes" :key="type.courseLabelId" :tab="type.courseLabelName">
                    <div class="h-150 overflow-auto">
                        <a-table
                        :columns="columns.optional"
                        :data-source="$store.state.commonLists.optionalCourses.find(item => item.courseLabelId === type.courseLabelId)?.courses"
                        :pagination="false"
                    >
                    </a-table>
                    </div>

                </a-tab-pane>
            </a-tabs>
        </div>
        <div v-else-if="selectedType === 'search'">
            <p>高级检索</p>
        </div>
    </div>
</template>

<script>
import axios from 'axios';

export default {
    data() {
        return {
            // 最外层选项卡
            selectedType: 'compulsory', // 必修 | 选修
            selectedOptionalType: '', // 选修课类型
            
            // 表格
            columns: {
                compulsory: [
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
                        dataIndex: 'facultyI18n',
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
                        align: 'center',
                        customRender: ({ text }) => text ? text.join('、') : ''
                    }
                ],
                optional: [
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
                        dataIndex: 'facultyI18n',
                        align: 'center'
                    },
                    {
                        title: '学分',
                        dataIndex: 'credit',
                        align: 'center'
                    },
                    {
                        title: '校区',
                        dataIndex: 'campus',
                        align: 'center',
                        customRender: ({ text }) => text ? text.join('、') : ''
                    }
                ]
            },
            selectedRowKeys: [],
        }
    },
    methods: {
        onSelectChange(selectedRowKeys, grade) {
            // Remove old selections for this grade
            this.selectedRowKeys = this.selectedRowKeys.filter(key => !key.startsWith(grade + '_'));
            // Add new selections
            this.selectedRowKeys = [...this.selectedRowKeys, ...selectedRowKeys];
            console.log('selectedRowKeys changed: ', this.selectedRowKeys);
        },
        async getOptionalCourses() {
            // 获取选修课程
            try {
                const res = await axios({
                    url: '/api/findOptionalCourseType',
                    method: 'post',
                    data: {
                        calendarId: this.$store.state.majorSelected.calendar
                    }
                });
                this.optionalTypes = this.$store.commit('setOptionalTypes', res.data.data);
            } catch (error) {
                console.log("error:", error);
            }

            // 获取选修课程具体信息
            try {
                const res = await axios({
                    url: '/api/findCourseByNatureId',
                    method: 'post',
                    data: {
                        calendarId: this.$store.state.majorSelected.calendar,
                        ids: this.$store.state.commonLists.optionalTypes.map(type => type.courseLabelId)
                    }
                });
                this.optionalCourses = this.$store.commit('setOptionalCourses', res.data.data);
            } catch (error) {
                console.log("error:", error);
            }
        }
    },
    mounted() {
        this.getOptionalCourses().then(() => {
            if (this.$store.state.commonLists.optionalTypes.length > 0) {
                this.selectedOptionalType = this.$store.state.commonLists.optionalTypes[0].courseLabelId;
            }
        });
    }
}
</script>