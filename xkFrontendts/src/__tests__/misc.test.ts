import { describe, it, expect } from 'vitest'
import { isUpToDate } from '../utils/misc'

describe('isUpToDate', () => {
    it('相同时间', () => {
        expect(isUpToDate('2026-06-27 13:45', '2026-06-27 13:45')).toBe(true)
    })
    it('时间不同', () => {
        expect(isUpToDate('2026-06-27 13:00', '2026-06-27 14:00')).toBe(false)
    })
    it('日期不同', () => {
        expect(isUpToDate('2026-06-26', '2026-06-27')).toBe(false)
    })
    it('空字符串', () => {
        expect(isUpToDate('', '2026-06-27')).toBe(false)
    })
})
