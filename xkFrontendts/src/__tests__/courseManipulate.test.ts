import { describe, it, expect } from 'vitest'
import { isSameCourse, canAddCourse, insertOccupied, deleteOccupied } from '../utils/courseManipulate'
import type { occupyCell, arrangementInfolet } from '../utils/myInterface'

function emptyOcc(): occupyCell[][][] {
    return Array(12).fill(null).map(() => Array(7).fill(undefined).map(() => []))
}

const CLASS_A: arrangementInfolet = {
    arrangementText: '星期一10-12节 [1-17] 南129\n', occupyDay: 1, occupyTime: [10, 11, 12],
    occupyWeek: [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17], occupyRoom: '南129',
    teacherAndCode: '刘庆(14508)',
}
const CLASS_A_ALT: arrangementInfolet = {
    arrangementText: '星期三5-6节 [1-17] 安楼B112\n', occupyDay: 3, occupyTime: [5, 6],
    occupyWeek: [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17], occupyRoom: '安楼B112',
    teacherAndCode: '黄超(19018)',
}
const CLASS_B: arrangementInfolet = {
    arrangementText: '星期四3-4节 [1-17] 安楼A204\n', occupyDay: 4, occupyTime: [3, 4],
    occupyWeek: [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17], occupyRoom: '安楼A204',
    teacherAndCode: '秦国锋(04171)',
}

describe('isSameCourse', () => {
    it('相同课号（忽略后两位班级序号）', () => {
        expect(isSameCourse('10038801', '10038802')).toBe(true)
    })
    it('不同课号', () => {
        expect(isSameCourse('10038801', '10016001')).toBe(false)
    })
    it('undefined 安全', () => {
        expect(isSameCourse(undefined as any, '10038801')).toBe(false)
        expect(isSameCourse('10038801', undefined as any)).toBe(false)
    })
})

describe('canAddCourse', () => {
    it('空课表可添加', () => {
        const result = canAddCourse([CLASS_A], emptyOcc(), '10038801')
        expect(result.canAdd).toBe(true)
    })
    it('同课号、同时段替换不冲突', () => {
        const o = emptyOcc()
        // 已经选了 10038802（和 10038801 同一时段 CLASS_A）
        insertOccupied(o, [CLASS_A], '10038802', '离散数学')
        // 用 10038801 替换 → 会先删除 10038802（同课号），再检查 → 无冲突
        const result = canAddCourse([CLASS_A], o, '10038801')
        expect(result.canAdd).toBe(true)
    })
    it('同课号换班——旧班占用释放，新班时段独立检查', () => {
        const o = emptyOcc()
        // 已有 10038802（周一10-12），想换成 10038801（周三5-6）
        insertOccupied(o, [CLASS_A], '10038802', '离散数学')
        // canAddCourse 发现同课号 → 先 deleteOccupied 释放周一
        // → 递归检查周三5-6 → 无占用 → 可添加
        const result = canAddCourse([CLASS_A_ALT], o, '10038801')
        expect(result.canAdd).toBe(true)
    })
    it('不同课号同时段冲突', () => {
        const o = emptyOcc()
        insertOccupied(o, [CLASS_A], '10016002', '计算机系统结构')
        const result = canAddCourse([CLASS_A], o, '10038801')
        expect(result.canAdd).toBe(false)
        expect(result.collideCourse).toContain('10016002')
    })
    it('不同天不冲突', () => {
        const o = emptyOcc()
        insertOccupied(o, [CLASS_B], '10016002', '计算机系统结构')
        const result = canAddCourse([CLASS_A], o, '10038801')
        expect(result.canAdd).toBe(true)
    })
})

describe('insertOccupied / deleteOccupied', () => {
    it('增删对称', () => {
        const o = emptyOcc()
        insertOccupied(o, [CLASS_A], '10038801', '离散数学')
        expect(o[9][0]).toHaveLength(1) // time=10 (index 9), day=1 (index 0)
        deleteOccupied(o, '10038801')
        expect(o[9][0]).toHaveLength(0)
    })
    it('deleteOccupied 按课号删除所有班级', () => {
        const o = emptyOcc()
        insertOccupied(o, [CLASS_A], '10038801', 'A')
        insertOccupied(o, [CLASS_A], '10038802', 'A2')
        deleteOccupied(o, '10038801')
        // isSameCourse 按课号（去掉后两位）比较，所以 10038801 和 10038802 都被删
        expect(o[9][0]).toHaveLength(0)
    })
    it('不同课号的课互不影响', () => {
        const o = emptyOcc()
        insertOccupied(o, [CLASS_A], '10038801', '离散数学')
        insertOccupied(o, [CLASS_B], '10016002', '计算机系统结构')
        deleteOccupied(o, '10038801')
        // 10016002 不受影响
        expect(o[9][0].some(c => c.code === '10016002')).toBe(false)
        expect(o[2][3].some(c => c.code === '10016002')).toBe(true) // day=4 time=3
    })
})
