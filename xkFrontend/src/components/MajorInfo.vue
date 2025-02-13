<template>
    <a-layout-content>
        <a-card
            title="专业选择"
        >
        <div class="flex flex-row space-x-8 items-center">
            <div class="flex flex-row space-x-4 items-center">
                <p>学期</p>
                <a-select
                    :value="selected.calendar"
                    placeholder="请选择学期"
                    @change="findGradeByCalendarId"
                    class="w-48"
                >
                    <a-select-option
                        v-for="calendar in rawList.calendars"
                        :value="calendar.calendarId"
                    >
                        {{ calendar.calendarName }}
                    </a-select-option>
                </a-select>
            </div>
            <div class="flex flex-row space-x-4 items-center">
                <p>年级</p>
                <a-select
                    :value="selected.grade"
                    placeholder="请选择年级"
                    @change="findMajorByGrade"
                    class="w-32"
                >
                    <a-select-option
                        v-for="grade in rawList.grades"
                        :value="grade"
                    >
                        {{ grade }}
                    </a-select-option>
                </a-select>
            </div>
            <div class="flex flex-row space-x-4 items-center">
                <p>专业</p>
                <a-select
                    :value="selected.major"
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
                        >
                            {{ major.name }}
                        </a-select-option>
                </a-select>
            </div>            
        </div>
        </a-card>
    </a-layout-content>
</template>

<script>
import axios from 'axios';

export default {
    data() {
        return {
            selected: {
                calendar: undefined,
                grade: undefined,
                major: undefined
            },
            rawList: {
                calendars: [],
                grades: [],
                majors: []
            },
        }
    },
    methods: {
        async getAllCalendar() {
            try {
                const res = await axios({
                    url: '/api/getAllCalendar',
                    method: 'get'
                });
                this.rawList.calendars = res.data.data;
            } catch (error) {
                console.log("error:", error);
            }
        },
        async findGradeByCalendarId(value) {
            this.selected.calendar = value;
            this.selected.grade = undefined;
            this.selected.major = undefined;
            try {
                const res = await axios({
                    url: '/api/findGradeByCalendarId',
                    method: 'post',
                    data: {
                        calendarId: this.selected.calendar
                    }
                });
                this.rawList.grades = res.data.data.gradeList;
                // 在年级更改时清空专业
                this.rawList.majors = [];
            } catch (error) {
                console.log("error:", error);
            }
        },
        async findMajorByGrade(value) {
            this.selected.grade = value;
            this.selected.major = undefined;
            try {
                const res = await axios({
                    url: '/api/findMajorByGrade',
                    method: 'post',
                    data: {
                        grade: this.selected.grade
                    }
                });
                this.rawList.majors = res.data.data;
            } catch (error) {
                console.log("error:", error);
            }
        },
        onMajorChange(value) {
            this.selected.major = value;
        },
        filterMajor(input, option) {
            return option.label.toLowerCase().indexOf(input.toLowerCase()) >= 0;
        }
    },
    mounted() {
        this.getAllCalendar();
    },
}
</script>
