"""US-5.1 — bckndTools.py 工具函数单元测试。"""

import pytest
from utils.bckndTools import (
    dayTextToNum,
    numToDayText,
    timeTextToArray,
    weekTextToArray,
    splitEndline,
    arrangementTextToObj,
    optCourseQueryListGenerator,
)


# ================================================================
#  dayTextToNum
# ================================================================

class TestDayTextToNum:
    def test_all_weekdays(self):
        assert dayTextToNum("星期一") == 1
        assert dayTextToNum("星期二") == 2
        assert dayTextToNum("星期三") == 3
        assert dayTextToNum("星期四") == 4
        assert dayTextToNum("星期五") == 5
        assert dayTextToNum("星期六") == 6
        assert dayTextToNum("星期日") == 7

    def test_invalid(self):
        assert dayTextToNum("星期八") is None
        assert dayTextToNum("Monday") is None
        assert dayTextToNum("") is None


# ================================================================
#  numToDayText
# ================================================================

class TestNumToDayText:
    def test_all_numbers(self):
        assert numToDayText(1) == "星期一"
        assert numToDayText(4) == "星期四"
        assert numToDayText(7) == "星期日"

    def test_invalid(self):
        assert numToDayText(0) is None
        assert numToDayText(8) is None


# ================================================================
#  timeTextToArray
# ================================================================

class TestTimeTextToArray:
    def test_normal(self):
        assert timeTextToArray("1-2节") == [1, 2]
        assert timeTextToArray("3-4节") == [3, 4]
        assert timeTextToArray("7-8节") == [7, 8]

    def test_wide_range(self):
        assert timeTextToArray("9-11节") == [9, 10, 11]
        assert timeTextToArray("1-4节") == [1, 2, 3, 4]

    def test_single_period(self):
        """3-3节 → [3]"""
        assert timeTextToArray("1-1节") == [1]
        assert timeTextToArray("3-3节") == [3]


# ================================================================
#  weekTextToArray
# ================================================================

class TestWeekTextToArray:
    def test_single_week(self):
        assert weekTextToArray("14") == [14]
        assert weekTextToArray("17") == [17]

    def test_range(self):
        assert weekTextToArray("1-16") == list(range(1, 17))
        assert weekTextToArray("5-6") == [5, 6]

    def test_odd_week(self):
        """1-15单 → [1, 3, 5, 7, 9, 11, 13, 15]"""
        assert weekTextToArray("1-15单") == [1, 3, 5, 7, 9, 11, 13, 15]
        assert weekTextToArray("1-7单") == [1, 3, 5, 7]

    def test_even_week(self):
        """2-16双 → [2, 4, 6, 8, 10, 12, 14, 16]"""
        assert weekTextToArray("2-16双") == [2, 4, 6, 8, 10, 12, 14, 16]

    def test_mixed_odd_even(self):
        """11-13单 14-16双"""
        result = weekTextToArray("11-13单 14-16双")
        assert result == [11, 13, 14, 16]

    def test_space_separated(self):
        """1 4 → [1, 4]"""
        assert weekTextToArray("1 4") == [1, 4]

    def test_complex(self):
        """混合：单双 + 范围 + 离散（函数 docstring 示例）"""
        result = weekTextToArray("2-4双 5-6 10-12 14 17")
        assert result == [2, 4, 5, 6, 10, 11, 12, 14, 17]


# ================================================================
#  splitEndline
# ================================================================

class TestSplitEndline:
    def test_single_line(self):
        result = splitEndline("王鑫(21075) 星期六7-8节 [1-15] 线上教室\n")
        assert result == ["王鑫(21075) 星期六7-8节 [1-15] 线上教室"]

    def test_multiline(self, sample_multiline):
        result = splitEndline(sample_multiline)
        assert len(result) == 5
        assert all("周玥" in line for line in result)

    def test_multiline_ends_with_newline(self):
        assert splitEndline("a\nb\n") == ["a", "b"]

    def test_trailing_only(self):
        """只有末尾换行的单行"""
        assert splitEndline("only one line\n") == ["only one line"]


# ================================================================
#  arrangementTextToObj
# ================================================================

class TestArrangementTextToObj:
    def test_normal(self, sample_normal):
        obj = arrangementTextToObj(sample_normal)
        assert obj["occupyDay"] == 6
        assert obj["occupyTime"] == [7, 8]
        assert obj["occupyWeek"] == [1, 3, 5, 7, 9, 11, 13, 15]
        assert obj["occupyRoom"] == "线上教室"
        assert obj["teacherAndCode"] == "王鑫(21075)"
        assert obj["arrangementText"] == "星期六7-8节 [1-15单] 线上教室"

    def test_multi_teacher(self, sample_multi_teacher):
        obj = arrangementTextToObj(sample_multi_teacher)
        assert obj["occupyDay"] == 1
        assert obj["occupyTime"] == [1, 2]
        assert obj["occupyWeek"] == [15]
        assert obj["occupyRoom"] == "沪西二教135阶梯教室"
        assert obj["teacherAndCode"] == "李姣(07085),高芙蓉(10017)"

    def test_many_teachers(self, sample_many_teachers):
        obj = arrangementTextToObj(sample_many_teachers)
        assert "惠英" in obj["teacherAndCode"]
        assert "Mohsen Alae" in obj["teacherAndCode"]
        assert obj["occupyDay"] == 3
        assert obj["occupyTime"] == [9, 10]

    def test_fudan_no_name(self, sample_fudan):
        """复旦格式：只有工号没有姓名"""
        obj = arrangementTextToObj(sample_fudan)
        assert obj["teacherAndCode"] == "(2400162),李奕滨(94431)"
        assert obj["occupyRoom"] == "复旦三教208"

    def test_fudan_fixed(self, sample_fudan_fixed):
        """复旦格式：已补全姓名"""
        obj = arrangementTextToObj(sample_fudan_fixed)
        assert obj["teacherAndCode"] == "寇宗来(2400162),李奕滨(94431)"

    def test_odd_week(self, sample_odd_week):
        obj = arrangementTextToObj(sample_odd_week)
        assert obj["occupyWeek"] == [1, 3, 5, 7]
        assert obj["occupyDay"] == 2

    def test_even_week(self, sample_even_week):
        obj = arrangementTextToObj(sample_even_week)
        assert obj["occupyWeek"] == [2, 4, 6, 8, 10, 12, 14, 16]

    def test_mixed_odd_even(self, sample_mixed_odd_even):
        obj = arrangementTextToObj(sample_mixed_odd_even)
        assert obj["occupyWeek"] == [11, 13, 14, 16]
        assert obj["occupyDay"] == 3

    def test_17weeks(self, sample_17weeks):
        """17 周满学期（旧制，1-17）"""
        obj = arrangementTextToObj(sample_17weeks)
        assert obj["occupyWeek"] == list(range(1, 18))
        assert obj["occupyDay"] == 3

    def test_17weeks_odd(self, sample_17weeks_odd):
        """17 周单周（1-17单 → 1,3,5,...,17）"""
        obj = arrangementTextToObj(sample_17weeks_odd)
        assert obj["occupyWeek"] == [1, 3, 5, 7, 9, 11, 13, 15, 17]
        assert obj["occupyDay"] == 2

    def test_17weeks_mixed(self, sample_17weeks_mixed):
        """混合：空间分隔离散 + 单周范围"""
        obj = arrangementTextToObj(sample_17weeks_mixed)
        assert obj["occupyWeek"] == [1, 2, 3, 4, 5, 6, 7, 15, 17]

    def test_17weeks_multiline(self, sample_17weeks_multiline):
        """17 周制多行排课"""
        lines = splitEndline(sample_17weeks_multiline)
        assert len(lines) == 2
        obj1 = arrangementTextToObj(lines[0])
        obj2 = arrangementTextToObj(lines[1])
        assert obj1["occupyWeek"] == list(range(2, 18))  # 2-17
        assert obj2["occupyWeek"] == [1, 3, 5, 7, 9, 11, 13, 15, 17]  # 1-17单

    def test_9_11_periods(self, sample_9_11_periods):
        obj = arrangementTextToObj(sample_9_11_periods)
        assert obj["occupyTime"] == [9, 10, 11]
        assert obj["occupyDay"] == 3

    def test_no_classroom(self, sample_no_classroom):
        obj = arrangementTextToObj(sample_no_classroom)
        assert obj["occupyRoom"] == "德国学校学习"
        assert obj["occupyDay"] == 5

    def test_empty(self):
        obj = arrangementTextToObj("")
        assert obj["occupyDay"] is None
        assert obj["occupyTime"] is None
        assert obj["occupyWeek"] is None
        assert obj["occupyRoom"] is None
        assert obj["teacherAndCode"] is None
        assert obj["arrangementText"] == ""

    def test_none(self):
        obj = arrangementTextToObj(None)
        assert obj["occupyDay"] is None

    def test_fudan_complex_room(self, sample_fudan_complex_room):
        """教室含中文括号、分号"""
        obj = arrangementTextToObj(sample_fudan_complex_room)
        assert "单周三" in obj["occupyRoom"]
        assert "双周三" in obj["occupyRoom"]
        assert "周五讨论" in obj["occupyRoom"]


# ================================================================
#  optCourseQueryListGenerator
# ================================================================

class TestOptCourseQueryListGenerator:
    def test_old_system(self, query_old_system_cases):
        for day, section, expected in query_old_system_cases:
            result = optCourseQueryListGenerator(day, section, calendarId=119)
            assert result[0] == expected, \
                f"day={day}, sec={section}: expected {expected}, got {result}"

    def test_new_system(self, query_new_system_cases):
        for day, section, expected in query_new_system_cases:
            result = optCourseQueryListGenerator(day, section, calendarId=120)
            assert result[0] == expected, \
                f"day={day}, sec={section}, cal=120: expected {expected}, got {result}"

    def test_boundary_invalid(self, query_boundary_cases):
        for day, section, cal in query_boundary_cases:
            assert optCourseQueryListGenerator(day, section, calendarId=cal) is None

    def test_exact_boundary_119_120(self):
        """calendarId 119 用旧制，120 用新制"""
        # Friday section 5
        old = optCourseQueryListGenerator(5, 5, calendarId=119)
        new = optCourseQueryListGenerator(5, 5, calendarId=120)
        assert old[0] == "%星期五9-%"       # 12节制：只有第9节
        assert new[0] == "%星期五9-1_%"     # 11节制：9-10节
