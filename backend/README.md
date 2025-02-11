# api

说明：所有的地址，不论语法如何，都**不加**复数；所有的键均使用 `camelCase`

## API 获得支持的所有学期

方法：`GET`

地址：`/api/getAllCalendar`

Response：

```json
{
    "code": 200,
    "msg": "查询成功",
    "data": [
            {
                "calendarId": 119,
                "calendarName": "2024-2025学年第2学期"
            },
            {
                "calendarId": 118,
                "calendarName": "2024-2025学年第1学期"
            },

            // ...

    ]
}
```

说明：降序排列，确保最新的学期在第 1 个(`data.[0]`)

## API 获得这一学期中所有的年级

方法：`POST`

地址：`/api/findGradeByCalendarId`

Payload：

```json
{
    "calendarId": 119
}
```

Response：

```json
{
    "code": 200,
    "msg": "查询成功",
    "data": {
        "gradeList": [2024, 2023, 2022, 2021, 2020, 2019]
    }
}
```

说明：降序排列。

## API 获得所有的可选专业

方法：`POST`

地址：`/api/findMajorByGrade`

Payload:

```json
{
    "grade": 2023
}
```

Response：

```json
{
    "code": 200,
    "msg": "查询成功",
    "data": {[
        {
            "code": "00304",
            "name": "2023(00304 基础学科拔尖基地(数学))"
        },
        {
            "code": "00402",
            "name": "2023(00402 基础学科拔尖基地(化学))"
        }

        // ...

    ]}
}
```

说明：升序，按 code 排序。

## API 通过专业查询所有专业课

方法：`POST`

地址：`/api/findCourseByMajor`

Payload：

```json
{
    "grade": 2023,
    "code": "10054"
}
```

Response：

```json
{
    "code": 200,
    "msg": "查询成功",
    "data": [
        {
            "courseCode": 102020,
            "courseName": "信息论及编码理论",
            "facultyI18n": "电子与信息工程学院",
            "grade": 2023,
            "courseNature": ["专业必修课"], // 有的课程可能存在相同课号多个性质的情况
            "courses": [
                {
                    "code": "10202005",
                    "campus": "嘉定校区",
                    "teachers": [
                        {
                            "teacherCode": "06019",
                            "teacherName": "万国春"
                        }
                    ],
                    "arragementInfo": [
                        {
                            "arrangementText": "星期四10-12节 [1-17] 安楼A205\n",
                            "occupyDay": 4,
                            "occupyTime": [10, 11, 12],
                            "occupyWeek": [
                                1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17
                            ],
                            "occupyRoom": "安楼A205"
                        }
                    ],
                    "isExclusive": 0
                },
                {
                    "code": "10202002",
                    "campus": "嘉定校区",
                    "teachers": [
                        {
                            "teacherCode": "00111",
                            "teacherName": "李宏强"
                        },
                        {
                            "teacherCode": "16509",
                            "teacherName": "武超"
                        }
                    ],
                    "arragementInfo": [
                        {
                            "arrangementText": "星期一5-6节 [1-2] 安楼A304\n",
                            "occupyDay": 1,
                            "occupyTime": [5, 6],
                            "occupyWeek": [
                                1, 2
                            ],
                            "occupyRoom": "安楼A304"
                        },
                        {
                            "arrangementText": "星期一5-6节 [3-17] 安楼A304\n",
                            "occupyDay": 1,
                            "occupyTime": [5, 6],
                            "occupyWeek": [
                                3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17
                            ],
                            "occupyRoom": "安楼A304"
                        },
                        {
                            "arrangementText": "星期四3-4节 [1] 安楼A304\n",
                            "occupyDay": 4,
                            "occupyTime": [3, 4],
                            "occupyWeek": [
                                1
                            ],
                            "occupyRoom": "安楼A304"
                        },
                        {
                            "arrangementText": "星期四3-4节 [3-17单] 安楼A304\n",
                            "occupyDay": 4,
                            "occupyTime": [3, 4],
                            "occupyWeek": [
                                3, 5, 7, 9, 11, 13, 15, 17
                            ],
                            "occupyRoom": "安楼A304"
                        }
                    ],
                    "isExclusive": 1
                },

                // ...

            ]
        }
    ]
}
```

## API 获得所有的选修课类别

方法：`POST`

地址：`/api/findOptionalCourseType`

Payload：

```json
{
    "calendarId": 119
}
```

Response：

```json
{
    "code": 200,
    "msg": "查询成功",
    "data": [
        {
            "courseLabelId": 958,
            "courseLabelName": "科学探索与生命关怀"
        },
        {
            "courseLabelId": 957,
            "courseLabelName": "社会发展与国际视野"
        },
        {
            "courseLabelId": 956,
            "courseLabelName": "工程能力与创新思维"
        },
        {
            "courseLabelId": 955,
            "courseLabelName": "人文经典与审美素养"
        },
        {
            "courseLabelId": 947,
            "courseLabelName": "通识选修课"
        }
    ]
}
```

## API 通过课程性质查询所有课程（只支持选修课）

方法：`POST`

地址：`/api/findCourseByNatureId`

Payload：

```json
{
    "ids": [958, 957, 956, 955, 947]
}
```

Response：

```json
{
    "code": 200,
    "msg": "查询成功",
    "data": [
        {
            "courseLabelId": 958,
            "courseLabelName": "科学探索与生命关怀",
            "courses": [
                {
                    "campus": [
                        "四平路校区"
                    ],
                    "courseCode": "140813",
                    "courseName": "海洋药物与健康",
                    "facultyI18n": "医学院"
                },
                {
                    "campus": [
                        "四平路校区"
                    ],
                    "courseCode": "140662",
                    "courseName": "五彩缤纷的发光材料",
                    "facultyI18n": "医学院"
                },
                {
                    "campus": [
                        "四平路校区"
                    ],
                    "courseCode": "140572",
                    "courseName": "人体生理学通识",
                    "facultyI18n": "医学院"
                },
                {
                    "campus": [
                        "四平路校区"
                    ],
                    "courseCode": "140496",
                    "courseName": "食品与健康",
                    "facultyI18n": "医学院"
                },
                {
                    "campus": [
                        "四平路校区"
                    ],
                    "courseCode": "140495",
                    "courseName": "食品安全导论",
                    "facultyI18n": "医学院"
                },
                {
                    "campus": [
                        "四平路校区"
                    ],
                    "courseCode": "140076",
                    "courseName": "公共营养学",
                    "facultyI18n": "医学院"
                },
                {
                    "campus": [
                        "嘉定校区",
                        "四平路校区"
                    ],
                    "courseCode": "124120",
                    "courseName": "物理现象探索",
                    "facultyI18n": "物理科学与工程学院"
                }

                // ...

            ]
        },
        {
            "courseLabelId": 957,
            "courseLabelName": "社会发展与国际视野",
            "courses": {[
                // ...
            ]}
        },

        // ...
        
    ]
}
```

说明：按 `courseLabelId` 降序返回。而每个 `courseLabelId` 内部的排序不能保证，如果必要的话，需要手动排序。返回的课程不包含具体的上课时间等信息，没必要。如果要获得选修课的信息，需要再用课号查询。

## API 通过课号获得课程的具体排课信息

方法：`POST`

地址：`/api/findCourseDetailByCode`

Payload：

```json
{
    "courseCode": "340012"
}
```

Response：

```json
{
    "code": 200,
    "msg": "查询成功",
    "data": {
        "code": "34001201",
        "teachers": [
            {
                "teacherCode": "13060",
                "teacherName": "李华"
            },
            {
                "teacherCode": "17076",
                "teacherName": "朱梦皎"
            }
        ],
        "campusI18n": "四平路校区",
        "arragementInfo": {
            {
                "arrangementText": "星期三7-8节 [2-4双 5-6 10-12 14 17] 北214\n",
                "occupyDay": 3,
                "occupyTime": [7, 8],
                "occupyWeek": [
                    2, 4, 5, 6, 10, 11, 12, 14, 17
                ],
                "occupyRoom": "北214"
            },
            {
                "arrangementText": "星期三7-8节 [1-3单 7-9 13-15单 16] 北214\n",
                "occupyDay": 3,
                "occupyTime": [7, 8],
                "occupyWeek": [
                    1, 3, 7, 8, 9, 13, 15, 16
                ],
                "occupyRoom": "北214"
            }
        }
    }
}
```

## API 高级检索课程

方法：`POST`

地址：`/api/findCourseBySearch`

Payload：

```json
{
    "calendarId": 119,
    "courseName": "上海",
    "courseCode": "",
    "teacherCode": "",
    "teacherName": "",
    "campus": "四平路校区",
    "faculty": ""
}
```

说明：

* 必须有 `calendarId`，其他字段至少有一个。

* 关于 `courseCode`，不管是否传入二位班级序号（如 `50002440016` 或 `5000244001601`），都可以检索。

* 为了方便添加课程，不提供太丰富的检索条件，且返回条数有上限：目前是 50 条。后续可能会动态调整。根据返回的字段来判断上限以及是否达到上限。

Response：

```json
{
    "code": 200,
    "msg": "查询成功",
    "data": {
        "courses": [
            {
                "courseCode": "50002950031",
                "courseName": "乡村振兴的上海图景认知",
                "facultyI18n": "马克思主义学院",
                "courseNature": ["社会发展与国际视野"],
                "campus_list": ["四平路校区"]
            },
            {
                "courseCode": "50002680134",
                "courseName": "学讲上海话",
                "facultyI18n": "外国语学院",
                "courseNature": ["人文经典与审美素养"],
                "campus_list": ["四平路校区"]
            },
            {
                "courseCode": "50001630031",
                "courseName": "上海城市空间认知",
                "facultyI18n": "建筑与城市规划学院",
                "courseNature": ["人文经典与审美素养"],
                "campus_list": ["四平路校区"]
            }
        ],
        "sizeLimit": 50,
    }
}
```
