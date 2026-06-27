"""Redis 热数据缓存 — 三级策略 + 自适应热度晋升。

三级缓存:
  static  — 永不过期，同步时主动清除（维度表、日历列表）
  hot     — 初始 2min TTL，5min 内命中 ≥3 次自动晋升为 1hr
  normal  — 固定 10min TTL，自然过期（搜索、详情）

Usage:
  from utils.redis_cache import cache_get, cache_set, cache_invalidate, cache_key

  # 读
  data = cache_get(cache_key(calendar_id, 'campuses'))
  if data is not None:
      return ok(data)

  # 写
  cache_set(cache_key(calendar_id, 'campuses'), result, 'static')
"""

import hashlib
import json
import logging

logger = logging.getLogger(__name__)


def _redis():
    """Lazy 获取 Redis 连接，避免 import 时序问题。"""
    from .redis_client import state
    return state.get('r')


def cache_key(calendar_id, resource, **params):
    """构建缓存 Key。

    Args:
        calendar_id: 学期 ID（meta 数据用 0）
        resource: 资源名（如 'campuses', 'courses'）
        **params: 查询参数（自动排序，MD5 压缩）

    Returns:
        str: 如 'cache:cal:119:campuses' 或 'cache:cal:119:courses:a3f8b2c1'
    """
    base = f"cache:cal:{calendar_id}:{resource}"
    if params:
        items = sorted(params.items())
        param_str = "_".join(f"{k}={v}" for k, v in items)
        param_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]
        return f"{base}:{param_hash}"
    return base


def cache_get(key):
    """读取缓存，自动追踪热度并晋升 TTL。

    - 每次命中：incr 热度计数器（窗口 5 分钟）
    - 达到 3 次命中：TTL 从初始 2min 晋升为 1hr

    Returns:
        反序列化后的数据，未命中返回 None。
    """
    r = _redis()
    if not r:
        return None
    try:
        val = r.get(key)
        if val:
            hot_key = f"{key}:h"
            hits = r.incr(hot_key)
            r.expire(hot_key, 300)           # 热度窗口 5min
            if hits >= 3:
                r.expire(key, 3600)          # 晋升 → 1hr
            return json.loads(val)
    except Exception:
        pass
    return None


def cache_set(key, value, strategy="normal"):
    """写入缓存。

    Args:
        key: 缓存键
        value: 任意 JSON 可序列化数据
        strategy: 'static' (永久) | 'hot' (2min) | 'normal' (10min)
    """
    r = _redis()
    if not r:
        return
    try:
        data = json.dumps(value, ensure_ascii=False)
        if strategy == "static":
            r.set(key, data)
        elif strategy == "hot":
            r.set(key, data, ex=120)
        elif strategy == "normal":
            r.set(key, data, ex=600)
        else:
            r.set(key, data, ex=300)  # fallback 5min
    except Exception:
        pass


def cache_invalidate(calendar_id):
    """清除指定学期的所有缓存（同步完成后调用）。

    Args:
        calendar_id: 要清除的学期 ID。
    """
    r = _redis()
    if not r:
        return
    try:
        pattern = f"cache:cal:{calendar_id}:*"
        deleted = 0
        for key in r.scan_iter(pattern):
            r.delete(key)
            deleted += 1
        if deleted:
            logger.info("已清除 %d 条缓存 (calendarId=%s)", deleted, calendar_id)
    except Exception:
        pass
