<template>
    <div
        class="flex flex-col w-full"
    >
        <div class="flex flex-row space-x-6 items-center mt-4 mb-4">
            <div>
                <a-radio-group v-model:value="selectedType" @change="$emit('update:selectedRowKeys', [])">
                <a-radio-button value="compulsory">计划内课程</a-radio-button>
                <a-radio-button value="optional">通识选修课</a-radio-button>
                <a-radio-button value="search">高级检索</a-radio-button>
            </a-radio-group>
            </div>
            <div>
                <a-input
                    placeholder="请输入课程代码或课程名称"
                    v-model:value="searchValue"
                    style="width: 250px"
                    allow-clear
                >
                    <template #prefix>
                        <SearchOutlined />
                    </template>
                </a-input>
            </div>
        </div>
        <div v-if="selectedType === 'compulsory'">
            <div class="h-150 overflow-auto">
                <a-table
                :columns="columns.compulsory"
                v-for="courses in this.$store.getters.sortCompulsoryCoursesByGrade"
                :data-source="filteredCourses(courses.courses)"
                :pagination="false"
                :title="() => courses.grade + '级'"
                :row-selection="{ 
                    localSelectedRowKeys: localSelectedRowKeys.filter(key => key.startsWith('必_' + courses.grade + '_')), 
                    onChange: (keys) => onCompulsorySelectChange(keys)
                }"
                :row-key="record => '必_' + courses.grade + '_' + record.courseCode"
                :row-class-name="(_record, index) => index % 2 === 1 ? 'bg-gray-50' : ''"
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
                        :data-source="filteredCourses($store.state.commonLists.optionalCourses.find(item => item.courseLabelId === type.courseLabelId)?.courses)"
                        :pagination="false"
                        :row-selection="{ 
                            localSelectedRowKeys: localSelectedRowKeys.filter(key => key.startsWith('选_' + type.courseLabelId + '_')), 
                            onChange: (keys) => onOptionalSelectChange(keys) 
                        }"
                        :row-key="record => '选_' + type.courseLabelId + '_' + record.courseCode"
                        :row-class-name="(_record, index) => index % 2 === 1 ? 'bg-gray-50' : ''"
                    >
                    </a-table>
                    </div>
                </a-tab-pane>
            </a-tabs>
        </div>
        <div v-else-if="selectedType === 'search'">
            <div>
                <p>高级检索</p>
            </div>
        </div>
    </div>
</template>

<script>
import axios from 'axios';
import { SearchOutlined } from '@ant-design/icons-vue';

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
                        dataIndex: 'faculty',
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

            // 搜索
            searchValue: ''
        }
    },
    props: ['selectedRowKeys'],
    methods: {
        onCompulsorySelectChange(localSelectedRowKeys) {
            this.localSelectedRowKeys = localSelectedRowKeys;
            // console.log('localSelectedRowKeys changed: ', this.localSelectedRowKeys);
        },
        onOptionalSelectChange(localSelectedRowKeys) {
            this.localSelectedRowKeys = localSelectedRowKeys;
            // console.log('localSelectedRowKeys changed: ', this.localSelectedRowKeys);
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
        },
        filteredCourses(courses) {
            // 根据已选课程来过滤，德摩根律啊！思考一下为什么是 && 而不是 ||
            courses = courses.filter((course) => {
                return !this.$store.state.commonLists.stagedCourses.some(stagedCourse => stagedCourse.courseCode === course.courseCode) 
                && !this.$store.state.commonLists.selectedCourses.some(selectedCourse => selectedCourse.courseCode === course.courseCode)
            });

            // 保留表格中和 this.searchValue 代码或者名称匹配的课程
            if (this.searchValue === '') {
                return courses;
            }
            else {
                // 根据检索条件过滤课程
                return courses.filter(course => course.courseCode.includes(this.searchValue) || course.courseName.includes(this.searchValue));
            }
        }
    },
    mounted() {
        this.getOptionalCourses().then(() => {
            if (this.$store.state.commonLists.optionalTypes.length > 0) {
                this.selectedOptionalType = this.$store.state.commonLists.optionalTypes[0].courseLabelId;
            }
        });
    },
    components: {
        SearchOutlined
    },
    computed: {
        localSelectedRowKeys: {
            get() {
                return this.selectedRowKeys;
            },
            set(value) {
                this.$emit('update:selectedRowKeys', value);
            }
        }
    }
}
</script>