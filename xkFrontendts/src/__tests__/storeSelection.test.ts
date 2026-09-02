import { describe, it, expect, vi, beforeEach } from 'vitest'

// store 引用了 ant-design-vue 的 message，测试中 mock 掉
vi.mock('../utils/notify', () => ({
    errorNotify: vi.fn(),
    successNotify: vi.fn(),
    infoNotify: vi.fn(),
    warningNotify: vi.fn(),
}))

import store from '../store/index'
import { CourseStatus, type arrangementInfolet, type courseDetaillet, type stagedCourse } from '../utils/myInterface'

// ---- localStorage 内存桩 ----
const mem = new Map<string, string>()
vi.stubGlobal('localStorage', {
    getItem: (k: string) => mem.get(k) ?? null,
    setItem: (k: string, v: string) => { mem.set(k, v) },
    removeItem: (k: string) => { mem.delete(k) },
    clear: () => { mem.clear() },
})

const CAL = 122

const ARR_A: arrangementInfolet = {
    arrangementText: '星期一1-2节 [1-17] 南101', occupyDay: 1, occupyTime: [1, 2],
    occupyWeek: [1], occupyRoom: '南101', teacherAndCode: '张三(00001)',
}
const ARR_B: arrangementInfolet = {
    arrangementText: '星期二3-4节 [1-17] 北201', occupyDay: 2, occupyTime: [3, 4],
    occupyWeek: [1], occupyRoom: '北201', teacherAndCode: '张三(00001)',
}

function mkDetail(code: string, arr: arrangementInfolet, status: CourseStatus = CourseStatus.Unselected): courseDetaillet {
    return {
        code,
        arrangementInfo: [arr],
        campus: '四平路校区',
        status,
        teachers: [{ teacherName: '张三', teacherCode: '00001' }],
        teachingLanguage: '中文',
    }
}

function mkStaged(detailA: courseDetaillet, detailB: courseDetaillet): stagedCourse {
    return {
        courseCode: '340012',
        courseName: '测试课程',
        courseNameReserved: '测试课程',
        credit: 2,
        courseType: '必修',
        teacher: [{ teacherName: '张三', teacherCode: '00001' }],
        status: CourseStatus.Unselected,
        courseDetail: [detailA, detailB],
    }
}

function snapSelected(): string[] {
    const raw = mem.get('solidified')
    expect(raw).toBeTruthy()
    return JSON.parse(raw!)[String(CAL)].selectedCourses
}

beforeEach(() => {
    mem.clear()
    store.commit('setMajorInfo', { calendarId: CAL, grade: 2026, major: '10054' })
    store.commit('clearAndSync')
    store.commit('setClickedCourseInfo', { courseCode: '340012', courseName: '测试课程' })
})

describe('saveSelectedCourses 去重', () => {
    it('已选班级换班后重新选回并保存，selectedCourses 不出现重复班号', () => {
        const detailA = mkDetail('34001201', ARR_A)
        const detailB = mkDetail('34001202', ARR_B)
        store.commit('pushStagedCourse', mkStaged(detailA, detailB))

        // 1. 点击班级 A → 保存课表
        store.commit('updateTimeTable', detailA)
        store.commit('saveSelectedCourses')
        store.commit('solidify')
        expect(store.state.commonLists.selectedCourses).toEqual(['34001201'])
        expect(snapSelected()).toEqual(['34001201'])

        // 2. 点击班级 B → 课程状态变为备选（A 仍为已选但不在课表上）
        store.commit('updateTimeTable', detailB)
        expect(store.state.commonLists.stagedCourses[0].status).toBe(CourseStatus.Staged)

        // 3. 再点击班级 A（重新选回）
        store.commit('updateTimeTable', detailA)
        expect(detailB.status).toBe(CourseStatus.Unselected)

        // 4. 再次保存课表
        store.commit('saveSelectedCourses')
        store.commit('solidify')

        // 内存与 localStorage 都不应有重复班号
        expect(store.state.commonLists.selectedCourses).toEqual(['34001201'])
        expect(snapSelected()).toEqual(['34001201'])
    })

    it('已选 A 换班为 B 并保存，A 被移除、B 加入', () => {
        const detailA = mkDetail('34001201', ARR_A)
        const detailB = mkDetail('34001202', ARR_B)
        store.commit('pushStagedCourse', mkStaged(detailA, detailB))

        store.commit('updateTimeTable', detailA)
        store.commit('saveSelectedCourses')
        store.commit('solidify')

        // 换班 B 后直接保存（不再点回 A）
        store.commit('updateTimeTable', detailB)
        store.commit('saveSelectedCourses')
        store.commit('solidify')

        expect(store.state.commonLists.selectedCourses).toEqual(['34001202'])
        expect(snapSelected()).toEqual(['34001202'])
        expect(detailA.status).toBe(CourseStatus.Unselected)
        expect(detailB.status).toBe(CourseStatus.Selected)
    })

    it('solidify 写入时自愈历史遗留的重复班号', () => {
        const detailA = mkDetail('34001201', ARR_A)
        store.commit('pushStagedCourse', mkStaged(detailA, mkDetail('34001202', ARR_B)))
        // 模拟老版本遗留的重复数据
        store.state.commonLists.selectedCourses = ['34001201', '34001201']
        store.commit('solidify')
        expect(snapSelected()).toEqual(['34001201'])
    })

    it('兼容旧版本 localStorage 快照（status 为纯数字）', () => {
        // 模拟旧版本持久化的快照：status 字段是纯数字，无枚举痕迹
        const oldSnap = {
            grade: 2026, major: '10054',
            stagedCourses: [{
                courseCode: '340012', courseName: '测试课程', courseNameReserved: '测试课程',
                credit: 2, courseType: '必修',
                teacher: [{ teacherName: '张三', teacherCode: '00001' }],
                status: 2,
                courseDetail: [{
                    code: '34001201', arrangementInfo: [ARR_A], campus: '四平路校区',
                    status: 2,
                    teachers: [{ teacherName: '张三', teacherCode: '00001' }],
                    teachingLanguage: '中文',
                }],
            }],
            selectedCourses: ['34001201'],
            updateTime: '2026-09-01 08:00',
        }
        mem.set('solidified', JSON.stringify({ [CAL]: oldSnap }))

        store.commit('loadSolidify')

        // 数字 2 与枚举成员相等 → 旧快照无需迁移即可正常使用
        const loaded = store.state.commonLists.stagedCourses[0]
        expect(loaded.status).toBe(CourseStatus.Selected)
        expect(loaded.courseDetail[0].status).toBe(CourseStatus.Selected)
        expect(store.state.commonLists.selectedCourses).toEqual(['34001201'])

        // 重新保存写回后 JSON 中仍是纯数字
        store.commit('solidify')
        const written = JSON.parse(mem.get('solidified')!)[String(CAL)]
        expect(written.stagedCourses[0].status).toBe(2)
        expect(written.stagedCourses[0].courseDetail[0].status).toBe(2)
    })
})
