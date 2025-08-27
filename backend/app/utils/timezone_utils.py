# -*- coding: utf-8 -*-
"""
时区处理工具函数
"""
from datetime import datetime, timezone, timedelta
from sqlalchemy.sql import func
from sqlalchemy.types import TypeDecorator, DateTime


# 北京时区
BEIJING_TZ = timezone(timedelta(hours=8))


def get_beijing_now():
    """获取当前北京时间"""
    return datetime.now(BEIJING_TZ)


def utc_to_beijing(utc_dt):
    """将UTC时间转换为北京时间"""
    if utc_dt is None:
        return None
    if utc_dt.tzinfo is None:
        # 假设为UTC时间
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    return utc_dt.astimezone(BEIJING_TZ)


def beijing_to_utc(beijing_dt):
    """将北京时间转换为UTC时间"""
    if beijing_dt is None:
        return None
    if beijing_dt.tzinfo is None:
        # 假设为北京时间
        beijing_dt = beijing_dt.replace(tzinfo=BEIJING_TZ)
    return beijing_dt.astimezone(timezone.utc)


class BeijingDateTime(TypeDecorator):
    """自定义DateTime类型，自动处理北京时区"""
    impl = DateTime
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        """存储到数据库时的处理"""
        if value is None:
            return value
        if isinstance(value, datetime):
            if value.tzinfo is None:
                # 无时区信息，假设为北京时间
                value = value.replace(tzinfo=BEIJING_TZ)
            # 转换为UTC存储
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value
    
    def process_result_value(self, value, dialect):
        """从数据库读取时的处理"""
        if value is None:
            return value
        if isinstance(value, datetime):
            # 数据库中存储的是UTC时间，转换为北京时间
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            return value.astimezone(BEIJING_TZ)
        return value


def beijing_now_func():
    """SQLAlchemy函数，返回当前北京时间对应的UTC时间"""
    return get_beijing_now().astimezone(timezone.utc).replace(tzinfo=None)