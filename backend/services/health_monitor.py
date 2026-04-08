"""
Health Monitor Service

数据源健康监控服务。
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from models import DataSourceHealth, db

logger = logging.getLogger(__name__)


class HealthMonitor:
    """
    健康监控器
    
    监控数据源状态：
    - 最后成功采集时间
    - 连续失败次数
    - 异常告警
    """
    
    FAILURE_THRESHOLD = 3  # 连续失败阈值
    STALE_THRESHOLD_HOURS = 48  # 过期阈值（小时）
    
    def record_success(self, source_name: str, source_type: str = "unknown"):
        """
        记录采集成功
        
        Args:
            source_name: 数据源名称
            source_type: 数据源类型 (rss, github, social, changelog)
        """
        try:
            health = DataSourceHealth.query.filter_by(source_name=source_name).first()
            
            if not health:
                health = DataSourceHealth(
                    source_name=source_name,
                    source_type=source_type
                )
                db.session.add(health)
            
            health.last_success_time = datetime.utcnow()
            health.consecutive_failures = 0
            health.status = 'healthy'
            health.last_error = None
            health.updated_at = datetime.utcnow()
            
            db.session.commit()
            logger.info(f"Recorded success for {source_name}")
        except Exception as e:
            logger.error(f"Failed to record success for {source_name}: {e}")
            db.session.rollback()
    
    def record_failure(self, source_name: str, error: str, source_type: str = "unknown"):
        """
        记录采集失败
        
        Args:
            source_name: 数据源名称
            error: 错误信息
            source_type: 数据源类型
        """
        try:
            health = DataSourceHealth.query.filter_by(source_name=source_name).first()
            
            if not health:
                health = DataSourceHealth(
                    source_name=source_name,
                    source_type=source_type
                )
                db.session.add(health)
            
            health.last_failure_time = datetime.utcnow()
            health.consecutive_failures += 1
            health.last_error = error[:1000]  # 限制错误信息长度
            health.updated_at = datetime.utcnow()
            
            # 根据连续失败次数更新状态
            if health.consecutive_failures >= self.FAILURE_THRESHOLD:
                health.status = 'error'
                logger.error(f"Data source {source_name} marked as ERROR after {health.consecutive_failures} consecutive failures")
            elif health.consecutive_failures > 1:
                health.status = 'warning'
                logger.warning(f"Data source {source_name} marked as WARNING after {health.consecutive_failures} consecutive failures")
            
            db.session.commit()
            logger.info(f"Recorded failure for {source_name} (consecutive: {health.consecutive_failures})")
        except Exception as e:
            logger.error(f"Failed to record failure for {source_name}: {e}")
            db.session.rollback()
    
    def get_source_health(self, source_name: str) -> Optional[Dict]:
        """
        获取数据源健康状态
        
        Returns:
            {
                "source_name": str,
                "status": "healthy" | "warning" | "error",
                "last_success": datetime,
                "consecutive_failures": int,
                "last_error": str
            }
        """
        try:
            health = DataSourceHealth.query.filter_by(source_name=source_name).first()
            if health:
                return health.to_dict()
            return None
        except Exception as e:
            logger.error(f"Failed to get health for {source_name}: {e}")
            return None
    
    def get_all_sources_health(self) -> List[Dict]:
        """获取所有数据源健康状态"""
        try:
            health_records = DataSourceHealth.query.all()
            return [h.to_dict() for h in health_records]
        except Exception as e:
            logger.error(f"Failed to get all sources health: {e}")
            return []
    
    def check_stale_sources(self, threshold_hours: int = None) -> List[str]:
        """
        检查过期数据源
        
        Args:
            threshold_hours: 过期阈值（小时），默认使用 STALE_THRESHOLD_HOURS
            
        Returns:
            过期数据源名称列表
        """
        if threshold_hours is None:
            threshold_hours = self.STALE_THRESHOLD_HOURS
        
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=threshold_hours)
            stale_sources = DataSourceHealth.query.filter(
                (DataSourceHealth.last_success_time < cutoff_time) |
                (DataSourceHealth.last_success_time.is_(None))
            ).all()
            
            stale_names = [s.source_name for s in stale_sources]
            
            if stale_names:
                logger.warning(f"Found {len(stale_names)} stale sources: {', '.join(stale_names)}")
            
            return stale_names
        except Exception as e:
            logger.error(f"Failed to check stale sources: {e}")
            return []
