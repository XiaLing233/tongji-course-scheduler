import { describe, it, expect } from 'vitest'
import { getRowSection } from '../utils/timetable'

describe('getRowSection', () => {
    describe('旧制 12 节课（calendarId < 120）', () => {
        const cal = 119
        it('1-2排 → 第1节', () => {
            expect(getRowSection(1, cal)).toBe(1)
            expect(getRowSection(2, cal)).toBe(1)
        })
        it('3-4排 → 第2节', () => {
            expect(getRowSection(3, cal)).toBe(2)
            expect(getRowSection(4, cal)).toBe(2)
        })
        it('5-6排 → 第3节', () => {
            expect(getRowSection(5, cal)).toBe(3)
            expect(getRowSection(6, cal)).toBe(3)
        })
        it('7-8排 → 第4节', () => {
            expect(getRowSection(7, cal)).toBe(4)
            expect(getRowSection(8, cal)).toBe(4)
        })
        it('9排 → 第5节', () => {
            expect(getRowSection(9, cal)).toBe(5)
        })
        it('10-12排 → 第6节', () => {
            expect(getRowSection(10, cal)).toBe(6)
            expect(getRowSection(11, cal)).toBe(6)
            expect(getRowSection(12, cal)).toBe(6)
        })
        it('无效排 → -1', () => {
            expect(getRowSection(0, cal)).toBe(-1)
            expect(getRowSection(13, cal)).toBe(-1)
        })
    })

    describe('新制 11 节课（calendarId >= 120）', () => {
        const cal = 120
        it('1-2排 → 第1节', () => {
            expect(getRowSection(1, cal)).toBe(1)
            expect(getRowSection(2, cal)).toBe(1)
        })
        it('9-10排 → 第5节', () => {
            expect(getRowSection(9, cal)).toBe(5)
            expect(getRowSection(10, cal)).toBe(5)
        })
        it('11排 → 第6节', () => {
            expect(getRowSection(11, cal)).toBe(6)
        })
        it('12排 → -1（11节制无第12排）', () => {
            expect(getRowSection(12, cal)).toBe(-1)
        })
    })
})
