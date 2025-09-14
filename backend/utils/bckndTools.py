# 存放了工具函数

def dayTextToNum(text):
    '''
    输入："星期一"
    输出：1
    从星期一到星期日对应 1 到 7
    '''
    day_mapping = {
        "星期一": 1,
        "星期二": 2,
        "星期三": 3,
        "星期四": 4,
        "星期五": 5,
        "星期六": 6,
        "星期日": 7
    }
    return day_mapping.get(text, None)

def numToDayText(num):
    '''
    输入：1
    输出："星期一"
    从 1 到 7 对应星期一到星期日
    '''
    day_mapping = {
        1: "星期一",
        2: "星期二",
        3: "星期三",
        4: "星期四",
        5: "星期五",
        6: "星期六",
        7: "星期日"
    }
    return day_mapping.get(num, None)

def timeTextToArray(text):
    '''
    输入："2-4节"
    输出：[2, 3, 4]
    '''
    # 忽略最后的节字
    text = text[:-1]
    
    # 以 - 分割
    time = text.split("-")
    
    # 转换为数字
    result = []
    for i in range(int(time[0]), int(time[1]) + 1):
        result.append(i)

    return result

def weekTextToArray(text):
    '''
    输入："2-4双 5-6 10-12 14 17"
    输出：[2, 4, 5, 6, 10, 11, 12, 14, 15, 16, 17]
    '''
    # 去掉中括号
    # text = text[1:-1]

    # 以空格分割
    weeks = text.split(" ")

    # 有这样几种类型
    # 没有 - 的，直接转换为数字，最简单
    # 有 -，且没有单/双，遍历区间
    # 有 -，如果有单/双，遍历区间，步长为 2，不需要判断单双是因为起始值已经保证了

    result = []

    for week in weeks:
        if "-" not in week:
            result.append(int(week))
        elif "单" in week or "双" in week:
            week = week[:-1]
            week = week.split("-")
            for i in range(int(week[0]), int(week[1]) + 1, 2):
                result.append(i)
        else:
            week = week.split("-")
            for i in range(int(week[0]), int(week[1]) + 1):
                result.append(i)
    
    return result

    

def arrangementTextToObj(text):
    '''
    输入："李华(13060) 星期三7-8节 [2-4双 5-6 10-12 14 17] 北214"
    输出：{
        "arrangementText": "星期三7-8节 [2-4双 5-6 10-12 14 17] 北214",
        "occupyDay": 3,
        "occupyTime": [7, 8],
        "occupyWeek": [2, 4, 5, 6, 10, 11, 12, 14, 17],
        "occupyRoom": "北214"
        "teacherAndCode": "李华(13060)"
    }
    '''

    # print(text)

    result = {
        "arrangementText": "星期" + text.split(" 星期", 1)[1],
        "occupyDay": None,
        "occupyTime": None,
        "occupyWeek": None,
        "occupyRoom": None,
        "teacherAndCode": text.split(" 星期", 1)[0].strip() # 对复旦的老师，似乎只有工号没有名字，要注意
    }


    # 星期几
    result["occupyDay"] = dayTextToNum("星期" + text.split(" 星期")[1][0])

    # 节次
    result["occupyTime"] = timeTextToArray(text.split(" 星期")[1][1:].split(" [")[0])

    # 周次
    result["occupyWeek"] = weekTextToArray(text.split("[")[1].split("]")[0])
    
    # 教室
    try:
        result["occupyRoom"] = text.split("] ")[1].strip()
    except:
        result["occupyRoom"] = None

    return result

def splitEndline(text):
    '''
    输入： "关佶红(05222) 星期一3-4节 [1-17] 南129\n关佶红(05222) 星期三3-4节 [1-17单] 北301\n"
    输出： ["关佶红(05222) 星期一3-4节 [1-17] 南129", "关佶红(05222) 星期三3-4节 [1-17单] 北301"]
    '''
    
    # print(text.split("\n")[:-1])

    return text.split("\n")[:-1]

def optCourseQueryListGenerator(day, section):
    '''
    输入：1
    输出："1-2"
    由于学校新作息删除了 12 节，且第 9 节开始排课，这段代码为了向后兼容前 4 年的数据，现在如此编写。未来可以想想更好的分组方式。
    现在的不足在于，对新学期的数据点击第 10 节和第 11 节，本来应该显示的课程不会显示。
    现在的迂回方式是，点击第 9 节可以获得完整的选修课数据，因为没有选修课从第 10 节开始。
    '''
    if section in [1, 2, 3, 4]:
        return ["%" + numToDayText(day) + str(2 * section - 1) + "-" + str(2 * section) + "%"]
    elif section == 5:
        return [f"%{numToDayText(day)}9-%"]
    elif section == 6:
        return [f"%{numToDayText(day)}10-11%", f"%{numToDayText(day)}10-12%"]
    else:
        return None


# debug

if __name__ == "__main__":
    # print(dayTextToNum("星期一"))
    # print(timeTextToArray(debugText))
    # print(weekTextToArray(debugText))
    # while True:
    debugText =  "关佶红(05222) 星期一3-4节 [1-17] 南129\n关佶红(05222) 星期三3-4节 [1-17单] 北301\n"
    print(splitEndline(debugText))
    for de in splitEndline(debugText):
        print(arrangementTextToObj(de))
