"""
工具函数
"""
from datetime import datetime, timezone

def get_current_utc_time():
    """获取当前 UTC 时间（兼容新旧 Python 版本）"""
    try:
        # Python 3.11+ 推荐方式
        return datetime.now(timezone.utc).replace(tzinfo=None)
    except:
        # 兼容旧版本
        return datetime.utcnow()
