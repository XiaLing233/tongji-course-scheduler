<template>
    <a-layout-content class="m-2">
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
                            @click="handleCellClick({ dayIndex, rowIndex: index })"
                        >
                            <div v-if="courses.length > 0" class="bg-indigo-700/90 text-white p-1 h-full rounded-b-xs overflow-x-hidden" :style="{ height: (maxSpans[index][dayIndex] * 45) + 'px' }">
                                <div v-for="(course, index) in courses" :key="course.code" class="text-xs h-full" :class="{ 'border-b border-dashed border-white pb-1 mb-1': index !== courses.length - 1 }">
                                    <span>{{ course.showText }}</span>
                                </div>
                            </div>
                        </td>
                    </template>
                </tr>
            </tbody>
        </table>
    </a-layout-content>
</template>

<script lang="ts">
import { errorNotify } from '@/utils/errorNotify';
import type { courseOnTable } from '@/utils/myInterface';

export default {
    name: 'timeTable',
    data() {
        return {
            timeTable: Array(12).fill(null).map(() => Array(7).fill(undefined).map(() => [])) as courseOnTable[][][],
            maxSpans: Array.from({ length: 12 }, () => Array(7).fill(1)),
            occupied: Array.from({ length: 12 }, () => Array(7).fill(false)), // 这个 occupied 表示的并不是一个单元格内有没有课程，而是这个单元格有没有被 startTime 不是这节课的课程占用
        }
    },
    methods: {
        getRowClass(index: number) {
            if (index === 11) return 'bg-red-50'
            return Math.floor(index / 2) % 2 === 0 ? 'bg-white' : 'bg-gray-50'
        },
        updateTimeTable() {
            // 初始化数据结构
            const newTimeTable = Array(12).fill(null).map(() => Array(7).fill(undefined).map(() => [])) as courseOnTable[][][]
            const newMaxSpans = Array.from({ length: 12 }, () => Array(7).fill(1))
            const newOccupied = Array.from({ length: 12 }, () => Array(7).fill(false))

            // 填充课程数据
            this.timeTableData.forEach((course: courseOnTable) => {
                const startRow = course.occupyTime[0] - 1
                const dayIndex = course.occupyDay - 1
                newTimeTable[startRow][dayIndex].push(course)
            })

            // 计算最大跨度
            for (let row = 0; row < 12; row++) {
                for (let col = 0; col < 7; col++) {
                    const courses = newTimeTable[row][col] // 同一个起始格可能会出现多个课程
                    if (courses.length > 0) {
                        newMaxSpans[row][col] = Math.max(...courses.map(c => c.occupyTime.length)) // 取最大跨度，不过注意在课程的排课上还是不要有交叉，如1-3,2-5，不好
                    }
                }
            }

            // 标记被占用的单元格
            for (let row = 0; row < 12; row++) {
                for (let col = 0; col < 7; col++) {
                    const span = newMaxSpans[row][col]
                    if (span > 1) {
                        for (let i = 1; i < span; i++) { // 也要把自己标进去呀，不知要标下方的，所以 i 从 0 开始
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
        },
        handleCellClick(cell: { dayIndex: number, rowIndex: number }) {
            // 如果输入了个人信息，再允许点击
            if (!this.$store.getters.isMajorSelected) {
                // console.log("未选择专业");
                errorNotify("未选择专业");
                return;
            }

            // 如果当前单元格没被占用，再触发事件
            if (this.$store.state.occupied[cell.rowIndex][cell.dayIndex].length > 0) {
                return
            }

            // 传入后，要 +1
            this.$emit('cellClick', { day: cell.dayIndex + 1, class: cell.rowIndex + 1 });
        }
    },
    computed: {
        timeTableData() {
            // console.log("tongbu", this.$store.state.timeTableData)
            return this.$store.state.timeTableData;
        }
    },
    watch: {
        timeTableData: {
            handler: 'updateTimeTable',
            immediate: true,
            deep: true // 不写这个的话，局部更新不会触发
        }
    },
    emits: ['cellClick'],
}
</script>