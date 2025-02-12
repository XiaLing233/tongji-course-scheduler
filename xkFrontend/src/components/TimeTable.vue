<template>
    <a-layout-content>
        <table class="w-full border-collapse border border-gray-300 table-fixed">
            <thead>
                <tr class="bg-gray-200">
                    <th class="border-collapse border border-gray-300 p-1">节次/周次</th>
                    <th v-for="day in ['一', '二', '三', '四', '五', '六', '日']" :key="day" class="border-collapse border border-gray-300 p-1">周{{ day }}</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="(row, index) in timeTable" :key="index" :class="getRowClass(index)">
                    <td class="border-collapse border border-gray-300 text-center h-[26px] p-1" :class="index == 11 ? 'text-red-500' : ''">第{{ index + 1 }}节课</td>
                    <template v-for="(courses, dayIndex) in row">
                        <td 
                            v-if="!occupied[index][dayIndex]"
                            :key="dayIndex"
                            class="border-collapse border border-gray-300 align-top text-center p-1"
                            :rowspan="maxSpans[index][dayIndex]"
                        >
                            <div v-if="courses.length > 0" class="bg-[#705bcf] text-white p-1 h-full rounded-b-xs overflow-x-hidden" :style="{ height: (maxSpans[index][dayIndex] * 45) + 'px' }">
                                <div v-for="(course, index) in courses" :key="course.id" class="text-xs h-full" :class="{ 'border-b border-dashed border-white pb-1 mb-1': index !== courses.length - 1 }">
                                    <span>{{ course.teacherName }} </span>
                                    <span>({{ course.teacherCode }}) </span>
                                    <span>{{ course.courseName }} </span>
                                    <span>({{ course.code }}) </span>
                                    <span>{{ course.arrangementText }}</span>
                                </div>
                            </div>
                        </td>
                    </template>
                </tr>
            </tbody>
        </table>
    </a-layout-content>
</template>

<script>
export default {
    name: 'timeTable',
    data() {
        return {
            timeTable: Array(12).fill(null).map(() => Array(7).fill().map(() => [])),
            maxSpans: Array.from({ length: 12 }, () => Array(7).fill(1)),
            occupied: Array.from({ length: 12 }, () => Array(7).fill(false)),
        }
    },
    props: {
        timeTableData: {
            type: Array,
            required: true
        }
    },
    methods: {
        getRowClass(index) {
            if (index === 11) return 'bg-red-50'
            return Math.floor(index / 2) % 2 === 0 ? 'bg-white' : 'bg-gray-50'
        },
        updateTimeTable() {
            // 初始化数据结构
            const newTimeTable = Array(12).fill(null).map(() => Array(7).fill().map(() => []))
            const newMaxSpans = Array.from({ length: 12 }, () => Array(7).fill(1))
            const newOccupied = Array.from({ length: 12 }, () => Array(7).fill(false))

            // 填充课程数据
            this.timeTableData.forEach(course => {
                const startRow = course.occupyTime[0] - 1
                const dayIndex = course.occupyDay - 1
                newTimeTable[startRow][dayIndex].push(course)
            })

            // 计算最大跨度
            for (let row = 0; row < 12; row++) {
                for (let col = 0; col < 7; col++) {
                    const courses = newTimeTable[row][col]
                    if (courses.length > 0) {
                        newMaxSpans[row][col] = Math.max(...courses.map(c => c.occupyTime.length))
                    }
                }
            }

            // 标记被占用的单元格
            for (let row = 0; row < 12; row++) {
                for (let col = 0; col < 7; col++) {
                    const span = newMaxSpans[row][col]
                    if (span > 1) {
                        for (let i = 1; i < span; i++) {
                            if (row + i < 12) {
                                newOccupied[row + i][col] = true
                            }
                        }
                    }
                }
            }

            // 更新响应式数据
            this.timeTable = newTimeTable
            this.maxSpans = newMaxSpans
            this.occupied = newOccupied
        }
    },
    watch: {
        timeTableData: {
            handler() {
                this.updateTimeTable()
            },
            immediate: true
        }
    }
}
</script>