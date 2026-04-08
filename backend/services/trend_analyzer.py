"""
Trend Analyzer Service

趋势分析服务，识别相似内容和热点方向。
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy import func
from models import ProductUpdate, db
from services.llm_analyzer import LLMAnalyzer

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """
    趋势分析器
    
    分析过去 30 天的更新，识别：
    - 相似主题的内容组
    - 热点功能方向
    - 竞品战略重点
    """
    
    def __init__(self, llm_analyzer: LLMAnalyzer = None):
        self.llm_analyzer = llm_analyzer or LLMAnalyzer()
    
    def analyze_trends(self, days: int = 30, min_updates: int = 5) -> List[Dict]:
        """
        分析趋势
        
        Args:
            days: 分析天数
            min_updates: 最小更新数量阈值
            
        Returns:
            趋势组列表，每个包含：
            - trend_title: 趋势标题
            - update_count: 更新数量
            - products: 涉及的产品列表
            - sample_updates: 示例更新
        """
        try:
            # 查询指定天数内的更新
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            updates = ProductUpdate.query.filter(
                ProductUpdate.publish_time >= cutoff_date
            ).order_by(ProductUpdate.publish_time.desc()).all()
            
            if len(updates) < min_updates:
                logger.info(f"Not enough updates ({len(updates)}) for trend analysis")
                return []
            
            # 准备数据给 LLM
            updates_data = [
                {
                    'title': u.title,
                    'content': u.content or "",
                    'product': u.product
                }
                for u in updates
            ]
            
            # 使用 LLM 分析趋势
            trends = self.llm_analyzer.analyze_trends(updates_data)
            
            logger.info(f"Identified {len(trends)} trends from {len(updates)} updates")
            return trends
        except Exception as e:
            logger.error(f"Trend analysis failed: {e}")
            return []
    
    def get_trending_tags(self, days: int = 30) -> List[Dict]:
        """
        获取热门标签
        
        Returns:
            标签统计列表，每个包含：
            - tag: 标签名称
            - count: 出现次数
            - products: 使用该标签的产品列表
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            updates = ProductUpdate.query.filter(
                ProductUpdate.publish_time >= cutoff_date,
                ProductUpdate.tags.isnot(None)
            ).all()
            
            # 统计标签
            tag_stats = {}
            for update in updates:
                tags = update.tags_list
                for tag in tags:
                    if tag not in tag_stats:
                        tag_stats[tag] = {
                            'tag': tag,
                            'count': 0,
                            'products': set()
                        }
                    tag_stats[tag]['count'] += 1
                    tag_stats[tag]['products'].add(update.product)
            
            # 转换为列表并排序
            result = []
            for tag_data in tag_stats.values():
                tag_data['products'] = list(tag_data['products'])
                result.append(tag_data)
            
            result.sort(key=lambda x: x['count'], reverse=True)
            
            logger.info(f"Found {len(result)} trending tags")
            return result
        except Exception as e:
            logger.error(f"Failed to get trending tags: {e}")
            return []
