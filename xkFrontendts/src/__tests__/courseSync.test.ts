/**
 * US-X — 课程同步逻辑测试。使用来自 calendar 118, major 10065, grade 2023 的真实数据。
 */
import { describe, it, expect } from 'vitest'
import {
    detectCourseChanges,
    applyCourseSync,
    rebuildOccupiedAndTimeTable,
    generateSyncMessage,
} from '../utils/courseSync'
import type {
    stagedCourse,
    occupyCell,
} from '../utils/myInterface'
import { CourseChangeType } from '../utils/myInterface'

// ── 辅助：浅拷贝 ──────────────────────────────────
function clone<T>(obj: T): T { return JSON.parse(JSON.stringify(obj)) }

// ── 来自真实 API 的排课数据 ───────────────────
const FIXTURE_DETAILS: Record<string, any[]> = {
    "100160": [
        {"code": "10016001", "campus": "四平路校区", "teachers": [{"teacherCode": "04171", "teacherName": "秦国锋"}], "teachingLanguage": "中文", "isExclusive": true, "arrangementInfo": [{"arrangementText": "星期四3-4节 [1-17] 安楼A204\\n", "occupyDay": 4, "occupyTime": [3, 4], "occupyWeek": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17], "occupyRoom": "安楼A204", "teacherAndCode": "秦国锋(04171)"}]},
        {"code": "10016002", "campus": "四平路校区", "teachers": [{"teacherCode": "93419", "teacherName": "陆建峰"}], "teachingLanguage": "中文", "isExclusive": true, "arrangementInfo": [{"arrangementText": "星期一10-12节 [1-17] 安楼F104\\n", "occupyDay": 1, "occupyTime": [10, 11, 12], "occupyWeek": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17], "occupyRoom": "安楼F104", "teacherAndCode": "陆建峰(93419)"}]},
    ],
    "100388": [
        {"code": "10038801", "campus": "四平路校区", "teachers": [{"teacherCode": "14508", "teacherName": "刘庆"}], "teachingLanguage": "中文", "isExclusive": true, "arrangementInfo": [{"arrangementText": "星期一10-12节 [1-17] 南129\\n", "occupyDay": 1, "occupyTime": [10, 11, 12], "occupyWeek": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17], "occupyRoom": "南129", "teacherAndCode": "刘庆(14508)"}]},
        {"code": "10038803", "campus": "四平路校区", "teachers": [{"teacherCode": "19018", "teacherName": "黄超"}], "teachingLanguage": "中文", "isExclusive": true, "arrangementInfo": [{"arrangementText": "星期三10-12节 [1-17] 安楼B112\\n", "occupyDay": 3, "occupyTime": [10, 11, 12], "occupyRoom": "安楼B112", "teacherAndCode": "黄超(19018)"}]},
        {"code": "10038804", "campus": "四平路校区", "teachers": [{"teacherCode": "10111", "teacherName": "陈志伟"}], "teachingLanguage": "中文", "isExclusive": true, "arrangementInfo": [{"arrangementText": "星期一3-4节 [1-17] 安楼A408\\n", "occupyDay": 1, "occupyTime": [3, 4], "occupyWeek": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17], "occupyRoom": "安楼A408", "teacherAndCode": "陈志伟(10111)"}]},
    ],
}

// ── 从 API 详情构建 stagedCourse ──────────────
function makeStagedCourses(): stagedCourse[] {
    return [
        {
            courseCode: '100160', courseName: '计算机系统结构(双语)', courseNameReserved: '计算机系统结构(双语)',
            credit: 3, courseType: '必修', status: 2,
            teacher: [{ teacherCode: '93419', teacherName: '陆建峰' }],
            courseDetail: FIXTURE_DETAILS['100160'].map((d: any) => ({
                code: d.code, campus: d.campus, teachers: d.teachers,
                teachingLanguage: d.teachingLanguage, isExclusive: d.isExclusive,
                arrangementInfo: d.arrangementInfo, status: d.code === '10016002' ? 2 : 0,
            })),
        },
        {
            courseCode: '100388', courseName: '离散数学', courseNameReserved: '离散数学',
            credit: 4, courseType: '必修', status: 2,
            teacher: [{ teacherCode: '14508', teacherName: '刘庆' }],
            courseDetail: FIXTURE_DETAILS['100388'].map((d: any) => ({
                code: d.code, campus: d.campus, teachers: d.teachers,
                teachingLanguage: d.teachingLanguage, isExclusive: d.isExclusive,
                arrangementInfo: d.arrangementInfo,
                status: d.code === '10038801' || d.code === '10038804' ? 2 : 0,
            })),
        },
    ]
}

// ── occupied 4×7 简化版 ─────────────────────────
function makeEmptyOccupied(): occupyCell[][][] {
    return Array(12).fill(null).map(() =>
        Array(7).fill(undefined).map(() => []))
}
function emptyOcc(): occupyCell[][][] { return makeEmptyOccupied() }


describe('detectCourseChanges', () => {
    it('无变更', () => {
        const oldCourses = makeStagedCourses()
        const occupied = makeEmptyOccupied()
        const result = detectCourseChanges(oldCourses, clone(oldCourses), ['10016002', '10038801'], occupied)
        expect(result.hasChanges).toBe(false)
        expect(result.changes).toHaveLength(0)
    })

    it('选中班级已关闭', () => {
        const oldCourses = makeStagedCourses()
        const newCourses = clone(oldCourses)
        // 删除已选班级 10038801 → 标记为 Closed
        newCourses[1].courseDetail = newCourses[1].courseDetail.filter((d: any) => d.code !== '10038801')
        // 同时删 teacher 中对应的（模拟 fetchLatestCourseInfo 行为）
        newCourses[1].teacher = []

        const result = detectCourseChanges(oldCourses, newCourses, ['10016002', '10038801'], makeEmptyOccupied())
        expect(result.hasChanges).toBe(true)
        const closed = result.changes.find(c => c.courseCode === '100388' && c.changeType === CourseChangeType.Closed)
        expect(closed).toBeDefined()
    })

    it('信息变更——教师更换', () => {
        const oldCourses = makeStagedCourses()
        const newCourses = clone(oldCourses)
        newCourses[0].teacher = [{ teacherCode: '99999', teacherName: '新老师' }]
        newCourses[0].courseDetail[1].teachers = [{ teacherCode: '99999', teacherName: '新老师' }]

        const result = detectCourseChanges(oldCourses, newCourses, ['10016002', '10038801'], makeEmptyOccupied())
        expect(result.hasChanges).toBe(true)
        const change = result.changes.find(c => c.courseCode === '100160')!
        expect(change.changeType).toBe(CourseChangeType.InfoChanged)
        // details 应包含教师变更信息
        expect(change.details).toContain('授课教师')
        // 不应包含排课变更信息
        expect(change.details).not.toContain('新增')
        expect(change.details).not.toContain('删除')
    })

    it('信息变更——排课时间变更（教师不变）', () => {
        const oldCourses = makeStagedCourses()
        const newCourses = clone(oldCourses)
        // 改 10038801 的节次：10-12 → 5-6，教师不变
        newCourses[1].courseDetail[0].arrangementInfo[0].occupyTime = [5, 6]

        const result = detectCourseChanges(oldCourses, newCourses, ['10016002', '10038801'], makeEmptyOccupied())
        expect(result.hasChanges).toBe(true)
        const change = result.changes.find(c => c.courseCode === '100388')!
        expect(change.changeType).toBe(CourseChangeType.InfoChanged)
        // details 应包含排课变更（修改/新增/删除），但不含教师变更
        expect(change.details).toContain('修改')
        expect(change.details).not.toContain('授课教师')
    })

    it('教师 + 排课同时变更', () => {
        const oldCourses = makeStagedCourses()
        const newCourses = clone(oldCourses)
        newCourses[0].teacher = [{ teacherCode: '99999', teacherName: '新老师' }]
        newCourses[0].courseDetail[1].teachers = [{ teacherCode: '99999', teacherName: '新老师' }]
        newCourses[0].courseDetail[1].arrangementInfo[0].occupyTime = [5, 6]

        const result = detectCourseChanges(oldCourses, newCourses, ['10016002', '10038801'], makeEmptyOccupied())
        expect(result.hasChanges).toBe(true)
        const change = result.changes.find(c => c.courseCode === '100160')!
        expect(change.changeType).toBe(CourseChangeType.InfoChanged)
        expect(change.details).toContain('授课教师')
        expect(change.details).toContain('修改')
    })

    it('isExclusive: true→false', () => {
        const oldCourses = makeStagedCourses()
        const newCourses = clone(oldCourses)
        newCourses[0].courseDetail[1].isExclusive = false
        const result = detectCourseChanges(oldCourses, newCourses, ['10016002', '10038801'], makeEmptyOccupied())
        expect(result.hasChanges).toBe(true)
        const change = result.changes[0]
        expect(change.changeType).toBe(CourseChangeType.InfoChanged)
        expect(change.details).toContain('专业课表状态')
        expect(change.details).not.toContain('授课教师')
    })

    it('isExclusive: false→true', () => {
        const oldCourses = makeStagedCourses()
        const altOld = clone(oldCourses)
        altOld[0].courseDetail[1].isExclusive = false
        const result = detectCourseChanges(altOld, oldCourses, ['10016002', '10038801'], makeEmptyOccupied())
        expect(result.hasChanges).toBe(true)
        const change = result.changes[0]
        expect(change.changeType).toBe(CourseChangeType.InfoChanged)
        expect(change.details).toContain('专业课表状态')
    })

    it('已选课新增班级——静默更新，不触发同步提醒', () => {
        const oldCourses = makeStagedCourses()
        const newCourses = clone(oldCourses)
        // 用户选了 10038801，后端返回时多了一个新班 10038820
        newCourses[1].courseDetail.push({
            code: '10038820', campus: '四平路校区',
            teachers: [{ teacherCode: '99999', teacherName: '新老师' }],
            teachingLanguage: '中文', isExclusive: true, arrangementInfo: [], status: 0,
        })
        // 已选班 10038801 没变 → 不触发变更
        const result = detectCourseChanges(oldCourses, newCourses, ['10016002', '10038801'], makeEmptyOccupied())
        expect(result.hasChanges).toBe(false)
    })

    it('冲突检测——变更后排课与另一已选课冲突', () => {
        const oldCourses = makeStagedCourses()
        // 选两个班：10016002(周一10-12) 和 10038804(周一3-4)，初始不冲突
        const selected = ['10016002', '10038804']

        // 用 rebuildOccupiedAndTimeTable 正规建 occupied（避免手工构造不合法状态）
        const { occupied: o } = rebuildOccupiedAndTimeTable(selected, oldCourses)

        // 变更 10038804 → 改为周一10-12，与 10016002 冲突
        const newCourses = clone(oldCourses)
        const class38804 = newCourses[1].courseDetail[2] // 10038804 是 index 2
        class38804.arrangementInfo[0].occupyDay = 1
        class38804.arrangementInfo[0].occupyTime = [10, 11, 12]

        const result = detectCourseChanges(oldCourses, newCourses, selected, o)
        expect(result.hasChanges).toBe(true)
        const conflict = result.changes.find(c => c.changeType === CourseChangeType.ConflictAfterUpdate)
        expect(conflict).toBeDefined()
        expect(conflict!.courseCode).toBe('100388')
    })
})

describe('applyCourseSync', () => {
    it('关课后删除', () => {
        const oldCourses = makeStagedCourses()
        const newCourses = clone(oldCourses)
        // 100388 关课
        const changes = [{
            courseCode: '100388',
            courseName: '离散数学',
            changeType: CourseChangeType.Closed as const,
        }]
        const result = applyCourseSync(changes, oldCourses, ['10016002', '10038801'], newCourses)
        expect(result.newStagedCourses).toHaveLength(1) // 只有 100160
        expect(result.newSelectedCodes).toEqual(['10016002']) // 100388 被移除
    })

    it('冲突后移至备选', () => {
        const oldCourses = makeStagedCourses()
        const newCourses = clone(oldCourses)
        const changes = [{
            courseCode: '100388',
            courseName: '离散数学',
            changeType: CourseChangeType.ConflictAfterUpdate as const,
            conflictWith: '计算机系统结构(双语)',
        }]
        const result = applyCourseSync(changes, oldCourses, ['10016002', '10038801'], newCourses)
        expect(result.newStagedCourses).toHaveLength(2)
        // 100388 还在 staged，但不在 selected
        expect(result.newSelectedCodes).toEqual(['10016002'])
    })
})

describe('rebuildOccupiedAndTimeTable', () => {
    it('从 selectedCodes 重建 occupied', () => {
        const courses = makeStagedCourses()
        const result = rebuildOccupiedAndTimeTable(['10016002'], courses)
        // 10016002: day=1, time=[10,11,12], 周次 1-17
        expect(result.timeTableData).toHaveLength(1)
        expect(result.timeTableData[0].occupyDay).toBe(1)
        expect(result.occupied[9][0]).toHaveLength(1) // time=10 → index 9
        expect(result.occupied[9][0][0].code).toBe('10016002')
    })
})

// ── 多时段教师边缘场景 ────────────────────────
const MULTISLOT_DETAIL = [
    {
        code: '10066301', campus: '四平路校区',
        teachers: [{ teacherCode: '05152', teacherName: '张亚英' }],
        teachingLanguage: '中文', isExclusive: true,
        arrangementInfo: [
            { arrangementText: '星期三1-2节 [1-17] 安楼A314\n', occupyDay: 3, occupyTime: [1, 2], occupyWeek: [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17], occupyRoom: '安楼A314', teacherAndCode: '张亚英(05152)' },
            { arrangementText: '星期四3-4节 [2-16双] 安楼A314\n', occupyDay: 4, occupyTime: [3, 4], occupyWeek: [2,4,6,8,10,12,14,16], occupyRoom: '安楼A314', teacherAndCode: '张亚英(05152)' },
        ],
    },
]

function makeMultiSlotCourse(): stagedCourse {
    return {
        courseCode: '100663', courseName: '数据结构与算法课程设计1', courseNameReserved: '数据结构与算法课程设计1',
        credit: 2, courseType: '必修', status: 2,
        teacher: [{ teacherCode: '05152', teacherName: '张亚英' }],
        courseDetail: MULTISLOT_DETAIL.map(d => ({
            code: d.code, campus: d.campus, teachers: d.teachers,
            teachingLanguage: d.teachingLanguage, isExclusive: d.isExclusive,
            arrangementInfo: d.arrangementInfo, status: 2,
        })),
    }
}

// ── 多教师共享时段 ────────────────────────────
function makeMultiTeacherCourse(): stagedCourse {
    return {
        courseCode: '999001', courseName: '多教师课', courseNameReserved: '多教师课',
        credit: 3, courseType: '必修', status: 2,
        teacher: [
            { teacherCode: 'A001', teacherName: '教师A' },
            { teacherCode: 'B001', teacherName: '教师B' },
        ],
        courseDetail: [{
            code: '99900101', campus: '四平路校区',
            teachers: [
                { teacherCode: 'A001', teacherName: '教师A' },
                { teacherCode: 'B001', teacherName: '教师B' },
            ],
            teachingLanguage: '中文', isExclusive: true, status: 2,
            arrangementInfo: [
                // 教师A: 周一3-4节，第1-5、7-16周
                { arrangementText: '', occupyDay: 1, occupyTime: [3, 4],
                  occupyWeek: [1,2,3,4,5,7,8,9,10,11,12,13,14,15,16],
                  occupyRoom: 'A101', teacherAndCode: '教师A(A001)' },
                // 教师B: 周三1-2节，第1-16周
                { arrangementText: '', occupyDay: 3, occupyTime: [1, 2],
                  occupyWeek: [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16],
                  occupyRoom: 'B201', teacherAndCode: '教师B(B001)' },
                // 教师B: 周一3-4节，第6周
                { arrangementText: '', occupyDay: 1, occupyTime: [3, 4],
                  occupyWeek: [6],
                  occupyRoom: 'A101', teacherAndCode: '教师B(B001)' },
            ],
        }],
    }
}

describe('多教师共享时段边缘情况', () => {
    it('时段数不变但周次重新分配', () => {
        const oldCourse = makeMultiTeacherCourse()
        const newCourse = clone(oldCourse)
        newCourse.courseDetail[0].arrangementInfo[0].occupyWeek = [1,2,3,4,5,16]
        newCourse.courseDetail[0].arrangementInfo[2].occupyWeek = [6,7,8,9,10,11,12,13,14,15]

        const result = detectCourseChanges([oldCourse], [newCourse], ['99900101'], emptyOcc())
        expect(result.hasChanges).toBe(true)
        const change = result.changes.find(c => c.courseCode === '999001')!
        expect(change.changeType).toBe(CourseChangeType.InfoChanged)
        // 教师没变，只变周次
        expect(change.details).toContain('修改')
        expect(change.details).not.toContain('授课教师')
    })

    it('教师B离职，时段转给教师A', () => {
        const oldCourse = makeMultiTeacherCourse()
        const newCourse = clone(oldCourse)
        const detail = newCourse.courseDetail[0]
        detail.arrangementInfo[0].occupyWeek = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]
        detail.arrangementInfo[1].teacherAndCode = '教师A(A001)'
        detail.arrangementInfo.splice(2, 1)
        detail.teachers = [{ teacherCode: 'A001', teacherName: '教师A' }]
        newCourse.teacher = [{ teacherCode: 'A001', teacherName: '教师A' }]

        const result = detectCourseChanges([oldCourse], [newCourse], ['99900101'], emptyOcc())
        expect(result.hasChanges).toBe(true)
        const change = result.changes.find(c => c.courseCode === '999001')!
        expect(change.changeType).toBe(CourseChangeType.InfoChanged)
        // 教师变了 + 排课变了
        expect(change.details).toContain('授课教师')
        expect(change.details).toContain('删除')  // 原B独有周一3-4被合并
    })

})

describe('单教师拆分为多教师', () => {
    it('新增教师接管原教师的整个时段', () => {
        const oldCourse = makeMultiSlotCourse()
        const newCourse = clone(oldCourse)
        const detail = newCourse.courseDetail[0]
        detail.teachers = [
            { teacherCode: '05152', teacherName: '张亚英' },
            { teacherCode: '99999', teacherName: '李四' },
        ]
        newCourse.teacher = [
            { teacherCode: '05152', teacherName: '张亚英' },
            { teacherCode: '99999', teacherName: '李四' },
        ]
        detail.arrangementInfo[1].teacherAndCode = '李四(99999)'

        const result = detectCourseChanges([oldCourse], [newCourse], ['10066301'], emptyOcc())
        expect(result.hasChanges).toBe(true)
        const change = result.changes[0]
        expect(change.changeType).toBe(CourseChangeType.InfoChanged)
        // 教师变了，teacherAndCode 也被 diffArrangements 检测为"修改"
        expect(change.details).toContain('授课教师')
        expect(change.details).toContain('修改')
    })

    it('新增教师只接管原教师的部分周次（细粒度拆分）', () => {
        const oldCourse = makeMultiSlotCourse()
        const newCourse = clone(oldCourse)
        const detail = newCourse.courseDetail[0]
        detail.teachers = [
            { teacherCode: '05152', teacherName: '张亚英' },
            { teacherCode: '99999', teacherName: '李四' },
        ]
        newCourse.teacher = [
            { teacherCode: '05152', teacherName: '张亚英' },
            { teacherCode: '99999', teacherName: '李四' },
        ]
        detail.arrangementInfo[1].occupyWeek = [2, 4, 6, 8, 10, 12]
        detail.arrangementInfo[1].teacherAndCode = '张亚英(05152)'
        detail.arrangementInfo.push({
            arrangementText: '', occupyDay: 4, occupyTime: [3, 4],
            occupyWeek: [14, 16], occupyRoom: '安楼A314',
            teacherAndCode: '李四(99999)',
        })

        const result = detectCourseChanges([oldCourse], [newCourse], ['10066301'], emptyOcc())
        expect(result.hasChanges).toBe(true)
        const change = result.changes[0]
        expect(change.changeType).toBe(CourseChangeType.InfoChanged)
        // 教师变了 + 排课变了（新增李四的时段 + 张亚英周次减少）
        expect(change.details).toContain('授课教师')
        expect(change.details).toContain('新增')
        expect(change.details).toContain('修改')
    })

})

describe('单教师单时段——教室变更', () => {
    it('全部周次换教室 → 识别为修改', () => {
        const oldCourse = makeMultiSlotCourse()
        const newCourse = clone(oldCourse)
        // 周三1-2，全17周从 A314 → B101
        newCourse.courseDetail[0].arrangementInfo[0].occupyRoom = 'B101'

        const result = detectCourseChanges([oldCourse], [newCourse], ['10066301'], emptyOcc())
        expect(result.hasChanges).toBe(true)
        const change = result.changes[0]
        expect(change.changeType).toBe(CourseChangeType.InfoChanged)
        expect(change.details).toContain('修改')
        expect(change.details).toContain('教室')
        expect(change.details).not.toContain('授课教师')
    })

    it('第15周换教室 → 拆分为修改+新增', () => {
        const oldCourse = makeMultiSlotCourse()
        const newCourse = clone(oldCourse)
        // 原：周三1-2，1-17周全在 A314
        // 新：周三1-2，1-14,16,17在 A314；第15周在 B101
        const arr = newCourse.courseDetail[0].arrangementInfo[0]
        arr.occupyWeek = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,16,17]
        arr.occupyRoom = '安楼A314'
        newCourse.courseDetail[0].arrangementInfo.push({
            arrangementText: '', occupyDay: 3, occupyTime: [1, 2],
            occupyWeek: [15], occupyRoom: 'B101',
            teacherAndCode: '张亚英(05152)',
        })

        const result = detectCourseChanges([oldCourse], [newCourse], ['10066301'], emptyOcc())
        expect(result.hasChanges).toBe(true)
        const change = result.changes[0]
        expect(change.changeType).toBe(CourseChangeType.InfoChanged)
        // 教师没变；原时段周次减少（修改）+ 新教室被识别为新增
        expect(change.details).toContain('修改')
        expect(change.details).toContain('新增')
        expect(change.details).toContain('周次')
        expect(change.details).not.toContain('授课教师')
    })
})

describe('单教师→四教师拆分（每人不同教室）', () => {
    it('1师变4师，各管4周，各用不同教室', () => {
        const oldCourse = makeMultiSlotCourse()
        const newCourse = clone(oldCourse)
        newCourse.courseDetail[0].teachers = [
            { teacherCode: 'T01', teacherName: '教师甲' },
            { teacherCode: 'T02', teacherName: '教师乙' },
            { teacherCode: 'T03', teacherName: '教师丙' },
            { teacherCode: 'T04', teacherName: '教师丁' },
        ]
        newCourse.teacher = [
            { teacherCode: 'T01', teacherName: '教师甲' },
            { teacherCode: 'T02', teacherName: '教师乙' },
            { teacherCode: 'T03', teacherName: '教师丙' },
            { teacherCode: 'T04', teacherName: '教师丁' },
        ]
        // 周三1-2 拆分：每人4周，各用不同教室
        newCourse.courseDetail[0].arrangementInfo = [
            { arrangementText: '', occupyDay: 3, occupyTime: [1, 2], occupyWeek: [1,2,3,4], occupyRoom: 'R101', teacherAndCode: '教师甲(T01)' },
            { arrangementText: '', occupyDay: 3, occupyTime: [1, 2], occupyWeek: [5,6,7,8], occupyRoom: 'R102', teacherAndCode: '教师乙(T02)' },
            { arrangementText: '', occupyDay: 3, occupyTime: [1, 2], occupyWeek: [9,10,11,12,13], occupyRoom: 'R103', teacherAndCode: '教师丙(T03)' },
            { arrangementText: '', occupyDay: 3, occupyTime: [1, 2], occupyWeek: [14,15,16,17], occupyRoom: 'R104', teacherAndCode: '教师丁(T04)' },
        ]

        const result = detectCourseChanges([oldCourse], [newCourse], ['10066301'], emptyOcc())
        expect(result.hasChanges).toBe(true)
        const change = result.changes[0]
        expect(change.changeType).toBe(CourseChangeType.InfoChanged)
        expect(change.details).toContain('授课教师')
        expect(change.details).toContain('新增')
        expect(change.details).toContain('删除')
        expect(change.details).toContain('教室')
    })
})

describe('教室合并', () => {
    it('多教室合并为单教室', () => {
        const oldCourse = makeMultiSlotCourse()
        const newCourse = clone(oldCourse)
        const detail = newCourse.courseDetail[0]
        // 原：周三1-2 在 A314（1-14,16,17周）+ 周四3-4双 在 A314
        // 模拟曾在周三1-2 [15] 用 B101，现在合并回 A314
        detail.arrangementInfo[0].occupyWeek = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17]
        detail.arrangementInfo[0].occupyRoom = '安楼A314'
        // 删除第二个教室的条目（合并）
        detail.arrangementInfo = [detail.arrangementInfo[0], detail.arrangementInfo[1]]

        // 先给 old "拆分"的状态（周三 + B101 一条）
        const splitOld = clone(oldCourse)
        splitOld.courseDetail[0].arrangementInfo[0].occupyWeek = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,16,17]
        splitOld.courseDetail[0].arrangementInfo.push({
            arrangementText: '', occupyDay: 3, occupyTime: [1, 2],
            occupyWeek: [15], occupyRoom: 'B101',
            teacherAndCode: '张亚英(05152)',
        })

        const result = detectCourseChanges([splitOld], [newCourse], ['10066301'], emptyOcc())
        expect(result.hasChanges).toBe(true)
        const change = result.changes[0]
        expect(change.changeType).toBe(CourseChangeType.InfoChanged)
        expect(change.details).toContain('删除')
        expect(change.details).not.toContain('授课教师')
    })
})

describe('多时段教师边缘情况', () => {
    it('教师不变，时段数减少（2→1）→ 应检测到变更', () => {
        const oldCourse = makeMultiSlotCourse()
        const newCourse = clone(oldCourse)
        // 删掉第二个时段（周四的课）
        newCourse.courseDetail[0].arrangementInfo = [newCourse.courseDetail[0].arrangementInfo[0]]

        const result = detectCourseChanges([oldCourse], [newCourse], ['10066301'], emptyOcc())
        expect(result.hasChanges).toBe(true)
        const change1 = result.changes[0]
        expect(change1.changeType).toBe(CourseChangeType.InfoChanged)
        expect(change1.details).toContain('删除')
        expect(change1.details).not.toContain('授课教师')
    })

    it('教师不变，时段完全一样 → 无变更', () => {
        const course = makeMultiSlotCourse()
        const result = detectCourseChanges([course], [clone(course)], ['10066301'], emptyOcc())
        expect(result.hasChanges).toBe(false)
    })

    it('教师不变，时段内容变化（节次/教室不同）', () => {
        const oldCourse = makeMultiSlotCourse()
        const newCourse = clone(oldCourse)
        newCourse.courseDetail[0].arrangementInfo[0].occupyTime = [5, 6]
        newCourse.courseDetail[0].arrangementInfo[0].occupyRoom = '新教室'

        const result = detectCourseChanges([oldCourse], [newCourse], ['10066301'], emptyOcc())
        expect(result.hasChanges).toBe(true)
        const change2 = result.changes[0]
        expect(change2.changeType).toBe(CourseChangeType.InfoChanged)
        expect(change2.details).toContain('修改')
        expect(change2.details).not.toContain('授课教师')
    })
})

describe('generateSyncMessage', () => {
    it('无变更', () => {
        expect(generateSyncMessage([])).toContain('均为最新')
    })
    it('有关课/冲突/变更', () => {
        const changes = [
            { courseCode: '100001', courseName: '课A', changeType: CourseChangeType.Closed as const },
            { courseCode: '100002', courseName: '课B', changeType: CourseChangeType.ConflictAfterUpdate as const, conflictWith: '课C' },
            { courseCode: '100003', courseName: '课D', changeType: CourseChangeType.InfoChanged as const, details: '教师变更' },
        ]
        const msg = generateSyncMessage(changes)
        expect(msg).toContain('已关课')
        expect(msg).toContain('冲突')
        expect(msg).toContain('已变更')
    })
})
