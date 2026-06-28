"""
统一 JSON 响应构建函数。

用法:
    from utils.response import ok, err, ok_paginated

    # 成功
    return ok(data)                           # → { code: 200, msg: "查询成功", data: ... }
    return ok(data, msg="自定义消息")
    return ok()                               # → { code: 200, msg: "查询成功", data: null }

    # 分页成功
    return ok_paginated(data, page=1, page_size=20, total=100)

    # 错误
    return err(400, "参数错误")
    return err(404, "记录不存在")
"""

from flask import jsonify


def ok(data=None, msg="查询成功"):
    """200 成功响应"""
    return jsonify({"code": 200, "msg": msg, "data": data}), 200


def ok_paginated(data, page, page_size, total, msg="查询成功"):
    """200 分页成功响应"""
    return jsonify({
        "code": 200,
        "msg": msg,
        "data": data,
        "pagination": {"page": page, "size": page_size, "total": total},
    }), 200


def err(code, msg):
    """错误响应"""
    return jsonify({"code": code, "msg": msg}), code
