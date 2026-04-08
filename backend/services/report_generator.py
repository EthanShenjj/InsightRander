"""
Report Generator Service

报告生成服务，生成周报和竞品对比。
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import func
from models import ProductUpdate, db
from services.llm_analyzer import LLMAnalyzer

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    报告生成器
    
    生成：
    - 周报（过去 7 天）
    - 竞品能力对比矩阵
    """
    
    def __init__(self, llm_analyzer: LLMAnalyzer = None):
        self.llm_analyzer = llm_analyzer or LLMAnalyzer()
    
    def generate_weekly_report(self) -> Dict:
        """
        生成周报
        
        Returns:
            周报数据，包含：
            - period: 时间范围
            - highlights: 重点更新
            - stats_by_product: 按产品统计
            - stats_by_type: 按类型统计
            - most_active_product: 最活跃产品
            - trending_categories: 热门类别
            - competitor_comparison: 竞品对比
            - trend_insights: 趋势洞察
        """
        try:
            # 查询过去 7 天的更新
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            updates = ProductUpdate.query.filter(
                ProductUpdate.publish_time >= cutoff_date
            ).order_by(ProductUpdate.publish_time.desc()).all()
            
            # 需求 6.7: 当过去 7 天没有更新，返回空周报提示
            if not updates:
                return {
                    "period": {
                        "start": cutoff_date.strftime('%Y-%m-%d'),
                        "end": datetime.utcnow().strftime('%Y-%m-%d')
                    },
                    "message": "No updates in the past 7 days",
                    "total_updates": 0,
                    "highlights": [],
                    "stats_by_product": {},
                    "stats_by_type": {},
                    "most_active_product": None,
                    "trending_categories": [],
                    "competitor_comparison": {},
                    "trend_insights": []
                }
            
            # 需求 6.4: 按产品分组展示更新统计
            stats_by_product = {}
            for update in updates:
                if update.product not in stats_by_product:
                    stats_by_product[update.product] = {
                        'count': 0,
                        'types': {}
                    }
                stats_by_product[update.product]['count'] += 1
                
                update_type = update.update_type or 'unknown'
                if update_type not in stats_by_product[update.product]['types']:
                    stats_by_product[update.product]['types'][update_type] = 0
                stats_by_product[update.product]['types'][update_type] += 1
            
            # 按类型统计
            stats_by_type = {}
            for update in updates:
                update_type = update.update_type or 'unknown'
                if update_type not in stats_by_type:
                    stats_by_type[update_type] = 0
                stats_by_type[update_type] += 1
            
            # 需求 6.5: 识别最活跃的产品
            most_active_product = max(
                stats_by_product.items(),
                key=lambda x: x[1]['count']
            )[0] if stats_by_product else None
            
            # 需求 6.6: 识别最热门的功能类别
            trending_categories = sorted(
                stats_by_type.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            
            # 选择重点更新（最近的 5 条）
            highlights = [
                {
                    'product': u.product,
                    'title': u.title,
                    'summary': u.summary or (u.content[:200] if u.content else ""),
                    'type': u.update_type,
                    'publish_time': u.publish_time.isoformat() if u.publish_time else None
                }
                for u in updates[:5]
            ]
            
            # 需求 6.3: 竞品对比部分
            competitor_comparison = self._generate_competitor_summary(updates)
            
            # 需求 6.3: 趋势洞察部分
            trend_insights = self._generate_trend_insights(updates)
            
            report = {
                "period": {
                    "start": cutoff_date.strftime('%Y-%m-%d'),
                    "end": datetime.utcnow().strftime('%Y-%m-%d')
                },
                "total_updates": len(updates),
                "highlights": highlights,
                "stats_by_product": stats_by_product,
                "stats_by_type": stats_by_type,
                "most_active_product": most_active_product,
                "trending_categories": [
                    {"category": cat, "count": count}
                    for cat, count in trending_categories
                ],
                "competitor_comparison": competitor_comparison,
                "trend_insights": trend_insights
            }
            
            logger.info(f"Generated weekly report with {len(updates)} updates")
            return report
        except Exception as e:
            logger.error(f"Failed to generate weekly report: {e}")
            return {
                "error": str(e),
                "period": {
                    "start": (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d'),
                    "end": datetime.utcnow().strftime('%Y-%m-%d')
                }
            }
    
    def generate_comparison_matrix(self) -> Dict:
        """
        生成竞品对比矩阵
        
        Returns:
            对比数据，包含：
            - matrix: {product: {tag: count}}
            - leaders: {tag: product}
            - summary: 总结文本列表
        """
        try:
            # 需求 7.1: 分析所有活跃竞品的历史更新
            updates = ProductUpdate.query.filter(
                ProductUpdate.tags.isnot(None)
            ).all()
            
            if not updates:
                return {
                    "matrix": {},
                    "leaders": {},
                    "all_tags": [],
                    "summary": []
                }
            
            # 需求 7.2: 基于 tags 字段统计每个竞品的功能覆盖
            matrix = {}
            all_tags = set()
            
            for update in updates:
                product = update.product
                if product not in matrix:
                    matrix[product] = {}
                
                tags = update.tags_list
                for tag in tags:
                    all_tags.add(tag)
                    if tag not in matrix[product]:
                        matrix[product][tag] = 0
                    matrix[product][tag] += 1
            
            # 需求 7.5: 标识每个功能领域的领先者
            leaders = {}
            for tag in all_tags:
                max_count = 0
                leader = None
                for product, tags_dict in matrix.items():
                    count = tags_dict.get(tag, 0)
                    if count > max_count:
                        max_count = count
                        leader = product
                if leader:
                    # 需求 7.5: leaders 格式为 {tag: product}
                    leaders[tag] = leader
            
            # 生成总结
            summary_lines = []
            for tag, leader in sorted(leaders.items(), key=lambda x: matrix[x[1]][x[0]], reverse=True)[:5]:
                count = matrix[leader][tag]
                summary_lines.append(
                    f"{leader} leads in {tag} with {count} updates"
                )
            
            # 需求 7.6: 返回 JSON 格式的对比表格数据
            result = {
                "matrix": matrix,
                "leaders": leaders,
                "all_tags": sorted(list(all_tags)),
                "summary": summary_lines
            }
            
            logger.info(f"Generated comparison matrix for {len(matrix)} products and {len(all_tags)} tags")
            return result
        except Exception as e:
            logger.error(f"Failed to generate comparison matrix: {e}")
            return {
                "error": str(e),
                "matrix": {},
                "leaders": {},
                "all_tags": [],
                "summary": []
            }
    
    def _generate_competitor_summary(self, updates: List) -> Dict:
        """
        生成竞品对比摘要（用于周报）
        
        Args:
            updates: 更新记录列表
            
        Returns:
            竞品对比摘要
        """
        # 按产品统计更新数量
        product_counts = {}
        product_tags = {}
        
        for update in updates:
            product = update.product
            if product not in product_counts:
                product_counts[product] = 0
                product_tags[product] = {}
            product_counts[product] += 1
            
            # 统计每个产品的标签分布
            for tag in update.tags_list:
                if tag not in product_tags[product]:
                    product_tags[product][tag] = 0
                product_tags[product][tag] += 1
        
        # 找出每个产品的主要关注领域
        product_focus = {}
        for product, tags in product_tags.items():
            if tags:
                top_tag = max(tags.items(), key=lambda x: x[1])
                product_focus[product] = {
                    "top_tag": top_tag[0],
                    "tag_count": top_tag[1]
                }
        
        return {
            "product_counts": product_counts,
            "product_focus": product_focus
        }
    
    def _generate_trend_insights(self, updates: List) -> List[Dict]:
        """
        生成趋势洞察（用于周报）
        
        Args:
            updates: 更新记录列表
            
        Returns:
            趋势洞察列表
        """
        # 统计标签趋势
        tag_counts = {}
        tag_products = {}
        
        for update in updates:
            for tag in update.tags_list:
                if tag not in tag_counts:
                    tag_counts[tag] = 0
                    tag_products[tag] = set()
                tag_counts[tag] += 1
                tag_products[tag].add(update.product)
        
        # 生成洞察
        insights = []
        for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            products = list(tag_products[tag])
            insights.append({
                "tag": tag,
                "count": count,
                "products": products,
                "insight": f"{tag} is trending with {count} updates across {len(products)} product(s)"
            })
        
        return insights