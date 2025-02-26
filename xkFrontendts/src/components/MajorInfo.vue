<template>
    <a-layout-content class="m-2">
        <a-card
            title="专业选择"
        >
        <div class="flex flex-row space-x-8 items-center">
            <div class="flex flex-row space-x-4 items-center">
                <p>学期</p>
                <a-select
                    :value="$store.state.majorSelected.calendarId"
                    placeholder="请选择学期"
                    @change="findGradeByCalendarId"
                    class="w-48"
                >
                    <a-select-option
                        v-for="calendar in rawList.calendars"
                        :value="calendar.calendarId"
                        :key="calendar.calendarId"
                    >
                        {{ calendar.calendarName }}
                    </a-select-option>
                </a-select>
            </div>
            <div class="flex flex-row space-x-4 items-center">
                <p>年级</p>
                <a-select
                    :value="$store.state.majorSelected.grade"
                    placeholder="请选择年级"
                    @change="findMajorByGrade"
                    class="w-32"
                >
                    <a-select-option
                        v-for="grade in rawList.grades"
                        :value="grade"
                        :key="grade"
                    >
                        {{ grade }}
                    </a-select-option>
                </a-select>
            </div>
            <div class="flex flex-row space-x-4 items-center">
                <p>专业</p>
                <a-select
                    :value="$store.state.majorSelected.major"
                    placeholder="请选择专业"
                    show-search
                    allow-clear
                    @change="onMajorChange"
                    class="w-100"
                    :filter-option="filterMajor"
                >
                    <a-select-option
                            v-for="major in rawList.majors"
                            :value="major.code"
                            :label="major.name"
                            :key="major.code"
                        >
                            {{ major.name }}
                        </a-select-option>
                </a-select>
            </div>            
        </div>
        </a-card>
    </a-layout-content>
</template>

<script lang="ts">
import axios from 'axios';
import { errorNotify } from '@/utils/errorNotify';

export default {
    data() {
        return {
            rawList: {
                calendars: [] as { calendarId: number, calendarName: string }[],
                grades: [],
                majors: [] as { code: string, name: string }[]
            }
        }
    },
    methods: {
        async getAllCalendar() {
            this.$store.commit("setSpin", true);

            try {
                const res = await axios({
                    url: '/api/getAllCalendar',
                    method: 'get'
                });
                this.rawList.calendars = res.data.data;
            }
            catch (error: any) {
                // console.log("error:", error);
                errorNotify(error.response.data.msg);
            }
            finally {
                this.$store.commit("setSpin", false);
            }
        },
        async findGradeByCalendarId(value: number) {
            this.$store.commit('setSpin', true);
            this.$store.commit('clearStagednSelectedCourses');
            this.$store.commit('setMajorInfo', 
                {
                    calendarId: value,
                    grade: undefined,
                    major: undefined
                }
            )
            try {
                const res = await axios({
                    url: '/api/findGradeByCalendarId',
                    method: 'post',
                    data: {
                        calendarId: this.$store.state.majorSelected.calendarId
                    }
                });
                this.rawList.grades = res.data.data.gradeList;
                // 在年级更改时清空专业
                this.rawList.majors = [];
            }
            catch (error: any) {
                // console.log("error:", error);
                errorNotify(error.response.data.msg);
            }
            finally {
                this.$store.commit('setSpin', false);
            }
        },
        async findMajorByGrade(value: number) {
            this.$store.commit('setSpin', true);
            this.$store.commit('clearStagednSelectedCourses');
            this.$store.commit('setMajorInfo', 
                {
                    calendarId: this.$store.state.majorSelected.calendarId,
                    grade: value,
                    major: undefined
                }
            )
            try {
                const res = await axios({
                    url: '/api/findMajorByGrade',
                    method: 'post',
                    data: {
                        grade: this.$store.state.majorSelected.grade
                    }
                });
                this.rawList.majors = res.data.data;
            }
            catch (error: any) {
                // console.log("error:", error);
                errorNotify(error.response.data.msg);
            }
            finally {
                this.$store.commit('setSpin', false);
            }
        },
        onMajorChange(value: string) {
            this.$emit('changeMajor')
            this.$store.commit('clearStagednSelectedCourses');
            this.$store.commit('setMajorInfo', 
                {
                    calendarId: this.$store.state.majorSelected.calendarId,
                    grade: this.$store.state.majorSelected.grade,
                    major: value
                }
            )
        },
        filterMajor(input: string, option: { label: string, value: string }) {
            return option.label.toLowerCase().indexOf(input.toLowerCase()) >= 0;
        }
    },
    async mounted() {
        await this.getAllCalendar()
        
        if (this.rawList.calendars.length > 0) {
            this.$store.commit('setMajorInfo', {
                calendarId: this.rawList.calendars[0].calendarId,
                grade: undefined,
                major: undefined
            });
            await this.findGradeByCalendarId(this.rawList.calendars[0].calendarId);
        }

        this.$store.commit("loadSolidify");

        if (this.$store.state.majorSelected.calendarId) {
            this.$store.commit('setSpin', true);
            try {
                const res = await axios({
                    url: '/api/findGradeByCalendarId',
                    method: 'post',
                    data: {
                        calendarId: this.$store.state.majorSelected.calendarId
                    }
                });
                this.rawList.grades = res.data.data.gradeList;
                // 在年级更改时清空专业
                this.rawList.majors = [];
            }
            catch (error: any) {
                // console.log("error:", error);
                errorNotify(error.response.data.msg);
            }
            finally {
                this.$store.commit('setSpin', false);
            }
        }

        if (this.$store.state.majorSelected.grade) {
            this.$store.commit('setSpin', true);
            try {
                const res = await axios({
                    url: '/api/findMajorByGrade',
                    method: 'post',
                    data: {
                        grade: this.$store.state.majorSelected.grade
                    }
                });
                this.rawList.majors = res.data.data;
            }
            catch (error: any) {
                errorNotify(error.response.data.msg);
            }
            finally {
                this.$store.commit('setSpin', false);
            }
        }
},
    emit: ['changeMajor']
}
</script>
