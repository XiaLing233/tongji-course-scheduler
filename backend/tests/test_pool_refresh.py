"""pool_refresh 监听器 — 纯单元测试（不需要 Redis/MySQL）。"""

from utils.pool_refresh import _handle_message


class FakeRouter:
    """记录 invalidate_pool 调用的假路由器。"""

    def __init__(self):
        self.invalidated = []

    def invalidate_pool(self, calendar_id):
        self.invalidated.append(calendar_id)


def test_handle_message_invalidates_pool():
    router = FakeRouter()
    _handle_message(router, '122')
    assert router.invalidated == [122]


def test_handle_message_ignores_garbage():
    router = FakeRouter()
    _handle_message(router, 'abc')
    assert router.invalidated == []


def test_handle_message_ignores_none():
    router = FakeRouter()
    _handle_message(router, None)
    assert router.invalidated == []
