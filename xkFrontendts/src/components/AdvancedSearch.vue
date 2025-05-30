<template>
    <div>
        <div class="flex flex-row flex-wrap gap-4 mb-4">
            <div class="w-90">
                <p>课程名称</p>
                <a-input v-model:value="searchBody.courseName" placeholder="请输入"/>
            </div>
            <div class="w-90">
                <p>课程代码</p>
                <a-input v-model:value="searchBody.courseCode" placeholder="请输入"/>
            </div>
            <div class="w-90">
                <p>教师工号</p>
                <a-input v-model:value="searchBody.teacherCode" placeholder="请输入"/>
            </div>
            <div class="w-90">
                <p>教师姓名</p>
                <a-input v-model:value="searchBody.teacherName" placeholder="请输入"/>
            </div>
            <div class="w-90">
                <p>校区</p>
                <a-select v-model:value="searchBody.campus" placeholder="请选择" class="w-full" show-search allow-clear>
                    <a-select-option v-for="campus in rawList.campus" :key="campus" :value="campus.campusName">{{ campus.campusName }}</a-select-option>
                </a-select>
            </div>
            <div class="w-90">
                <p>开课学院</p>
                <a-select v-model:value="searchBody.faculty" placeholder="请选择" class="w-full" show-search allow-clear>
                    <a-select-option v-for="faculty in rawList.faculty" :key="faculty" :value="faculty.facultyName">{{ faculty.facultyName }}</a-select-option>
                </a-select>
            </div>
        </div>
        <div class="mb-4">
            <a-button type="primary" @click="findCourseBySearch">搜索</a-button>
        </div>
        <div class="h-110 overflow-auto">
            <a-table
                        :columns="searchColumn"
                        :data-source="filteredCourses($store.state.commonLists.searchCourses)"
                        :pagination="false"
                        :row-selection="{ 
                            selectedRowKeys: localSelectedRowKeys.filter((key: string) => key.startsWith('查' + '_')), 
                            onChange: (keys: string[]) => onSearchSelectChange(keys) 
                        }"
                        :row-key="(record: any) => '查' + '_' + record.courseCode"
                        :row-class-name="(_record: string, index: number) => index % 2 === 1 ? 'bg-gray-50' : ''"
                    >
                    </a-table>
        </div>
    </div>
</template>


<script lang="ts">
import axios from 'axios';
import { errorNotify } from '@/utils/errorNotify';
import type { courseInfo, stagedCourse, rawCampus, rawFaculty } from '@/utils/myInterface';

export default {
    data() {
        return {
            searchBody: {
                calendarId: this.$store.state.majorSelected.calendarId,
                courseName: '',
                courseCode: '',
                teacherCode: '',
                teacherName: '',
                campus: undefined,
                faculty: undefined
            },
            rawList: {
                campus: [] as rawCampus[],
                faculty: [] as rawFaculty[]
            },
            searchColumn: [
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
                        customRender: ({ text }: { text: string[] }) => text ? text.join('、') : ''
                    },
                    {
                        title: '校区',
                        dataIndex: 'campus',
                        align: 'center',
                        customRender: ({ text }: { text: string[] }) => text ? text.join('、') : ''
                    }
                ],
        }
    },
    methods: {
        async getAllCampus () {
            this.$store.commit('setSpin', true);

            try {
                const res = await axios.get('/api/getAllCampus');
                this.rawList.campus = res.data.data;
            }
            catch (error: any) {
                errorNotify(error.response.data.msg);
            }
            finally {
                this.$store.commit('setSpin', false);
            }
        },

        async getAllFaculty () {
            this.$store.commit('setSpin', true);

            try {
                const res = await axios.get('/api/getAllFaculty');
                this.rawList.faculty = res.data.data;
            }
            catch (error: any) {
                errorNotify(error.response.data.msg);
            }
            finally {
                this.$store.commit('setSpin', false);
            }
        },
        
        async findCourseBySearch() {
            this.$store.commit('setSpin', true);

            try {
                const searchData = { ...this.searchBody } as any;
                for (let key in searchData) {
                    if (searchData[key] === undefined) {
                        searchData[key] = '';
                    }
                }
                const res = await axios({
                    url: '/api/findCourseBySearch',
                    method: 'post',
                    data: searchData
                });
                // console.log(res.data.data);
                this.$store.commit('setSearchedCourses', res.data.data.courses);

                // 如果搜索内容超过了阈值
                if (res.data.data.courses.length >= res.data.data.sizeLimit) {
                    errorNotify('搜索结果过多，只展示了前' + res.data.data.sizeLimit + '条');
                }
                else {
                    console.log("OK");
                }
            }
            catch (error: any) {
                errorNotify(error.response.data.msg);
            }
            finally {
                this.$store.commit('setSpin', false);
            }
        },
        filteredCourses(courses: courseInfo[]) {
            // console.log(courses);
            // 根据已选课程来过滤，德摩根律啊！思考一下为什么是 && 而不是 ||
            courses = courses.filter((course) => {
                return !this.$store.state.commonLists.stagedCourses.some((stagedCourse: stagedCourse) => stagedCourse.courseCode === course.courseCode);
            });

            // 保留表格中和 this.searchValue 代码或者名称匹配的课程
            if (this.searchValue === '') {
                return courses;
            }
            else {
                // 根据检索条件过滤课程
                return courses.filter(course => course.courseCode.includes(this.searchValue) || course.courseName.includes(this.searchValue));
            }
        },
        onSearchSelectChange(localSelectedRowKeys: string[]) {
            this.localSelectedRowKeys = localSelectedRowKeys;
        },
    },
    mounted() {
        this.getAllCampus();
        this.getAllFaculty();
    },
    props: ['searchValue', 'selectedRowKeys'],
    computed: {
        localSelectedRowKeys: {
            get() {
                return this.selectedRowKeys;
            },
            set(val: string[]) {
                // console.log("更新：", val);
                this.$emit('update:selectedRowKeys', val);
            }
        }
    }   
}

</script>