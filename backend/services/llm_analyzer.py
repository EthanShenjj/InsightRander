"""
LLM Analyzer Service

统一的 LLM 分析服务，封装所有与 OpenAI 兼容 API 的交互。
支持内容分类、标签生成、摘要生成和趋势分析。
"""

import os
import time
import logging
from typing import List, Dict, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


class LLMAnalyzer:
    """
    LLM 分析服务
    
    提供统一的 LLM 调用接口，支持：
    - 内容分类
    - 标签生成
    - 摘要生成
    - 趋势分析
    """
    
    # 预定义标签
    PREDEFINED_TAGS = [
        "A/B Testing", "Funnel", "Session Replay", "AI Insights",
        "Data Warehouse", "Real-time Analytics", "User Segmentation",
        "Retention Analysis", "Cohort Analysis", "Product Analytics"
    ]
    
    # 分类类型
    CLASSIFICATION_TYPES = ["feature", "bug", "ai", "pricing", "strategy"]
    
    def __init__(self):
        """初始化 LLM 客户端"""
        self.api_base = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')
        self.api_key = os.getenv('OPENAI_API_KEY', '')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        self.timeout = int(os.getenv('OPENAI_TIMEOUT', '30'))
        self.max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', '1000'))
        
        # 配置验证
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not configured. LLM features will use fallback strategies.")
            self.client = None
        else:
            try:
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.api_base,
                    timeout=self.timeout
                )
                logger.info(f"LLM Analyzer initialized with model: {self.model}")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
    
    def classify_content(self, title: str, content: str) -> str:
        """
        分类内容类型
        
        Args:
            title: 标题
            content: 内容
            
        Returns:
            分类结果 (feature/bug/ai/pricing/strategy)
        """
        if not self.client:
            return self._fallback_classify(title, content)
        
        prompt = f"""Classify the following product update into one of these categories: {', '.join(self.CLASSIFICATION_TYPES)}.

Title: {title}
Content: {content[:500]}

Respond with only the category name, nothing else."""
        
        try:
            result = self._call_llm([{"role": "user", "content": prompt}], temperature=0.3)
            result = result.strip().lower()
            
            # 验证返回值
            if result in self.CLASSIFICATION_TYPES:
                return result
            else:
                logger.warning(f"Invalid classification result: {result}, using fallback")
                return self._fallback_classify(title, content)
        except Exception as e:
            logger.error(f"Classification failed: {e}, using fallback")
            return self._fallback_classify(title, content)
    
    def generate_tags(self, title: str, content: str, update_type: str) -> List[str]:
        """
        生成智能标签
        
        Args:
            title: 标题
            content: 内容
            update_type: 更新类型
            
        Returns:
            标签列表（最多 5 个）
        """
        if not self.client:
            return self._fallback_generate_tags(title, content)
        
        tags_str = ', '.join(self.PREDEFINED_TAGS)
        prompt = f"""Based on the following product update, select up to 5 most relevant tags from this list: {tags_str}

Title: {title}
Content: {content[:500]}
Type: {update_type}

Respond with only the tag names separated by commas, nothing else."""
        
        try:
            result = self._call_llm([{"role": "user", "content": prompt}], temperature=0.3)
            tags = [tag.strip() for tag in result.split(',')]
            
            # 过滤并验证标签
            valid_tags = [tag for tag in tags if tag in self.PREDEFINED_TAGS]
            return valid_tags[:5]
        except Exception as e:
            logger.error(f"Tag generation failed: {e}, using fallback")
            return self._fallback_generate_tags(title, content)
    
    def generate_summary(self, content: str, max_length: int = 200) -> str:
        """
        生成内容摘要
        
        Args:
            content: 原始内容
            max_length: 最大长度
            
        Returns:
            摘要文本
        """
        # 如果内容本身就很短，直接返回
        if len(content) <= max_length:
            return content
        
        if not self.client:
            return self._fallback_summary(content, max_length)
        
        prompt = f"""Summarize the following content in no more than {max_length} characters. Be concise and focus on key points.

Content: {content[:1000]}

Summary:"""
        
        try:
            result = self._call_llm([{"role": "user", "content": prompt}], temperature=0.5)
            summary = result.strip()
            
            # 确保不超过最大长度
            if len(summary) > max_length:
                summary = summary[:max_length-3] + "..."
            
            return summary
        except Exception as e:
            logger.error(f"Summary generation failed: {e}, using fallback")
            return self._fallback_summary(content, max_length)
    
    def analyze_trends(self, updates: List[Dict]) -> List[Dict]:
        """
        分析趋势和聚类
        
        Args:
            updates: 更新记录列表，每个包含 title, content, product
            
        Returns:
            趋势组列表
        """
        if not self.client or len(updates) < 5:
            return []
        
        # 构建更新摘要
        updates_summary = "\n".join([
            f"{i+1}. [{u.get('product')}] {u.get('title')}"
            for i, u in enumerate(updates[:50])  # 限制最多 50 条
        ])
        
        prompt = f"""Analyze the following product updates and identify up to 10 major trends or themes. Group similar updates together.

Updates:
{updates_summary}

For each trend, provide:
1. A descriptive title
2. The update numbers that belong to this trend (comma-separated)

Format your response as:
Trend: [Title]
Updates: [numbers]

Trend: [Title]
Updates: [numbers]"""
        
        try:
            result = self._call_llm([{"role": "user", "content": prompt}], temperature=0.5)
            return self._parse_trends(result, updates)
        except Exception as e:
            logger.error(f"Trend analysis failed: {e}")
            return []
    
    def _call_llm(self, messages: List[Dict], temperature: float = 0.3, max_retries: int = 2) -> str:
        """
        调用 LLM API（内部方法）
        
        包含重试逻辑和错误处理
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_retries: 最大重试次数（默认 2 次）
            
        Returns:
            LLM 响应文本
            
        Raises:
            Exception: 当所有重试都失败时
        """
        if not self.client:
            raise Exception("LLM client not initialized")
        
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=self.max_tokens
                )
                return response.choices[0].message.content
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    wait_time = 60  # 固定 1 分钟间隔
                    logger.warning(f"LLM call failed (attempt {attempt + 1}/{max_retries + 1}): {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
        
        raise last_error
    
    def _fallback_classify(self, title: str, content: str) -> str:
        """降级分类策略：使用关键词匹配"""
        text = (title + " " + content).lower()
        
        if any(kw in text for kw in ["ai", "gpt", "machine learning", "ml", "artificial intelligence"]):
            return "ai"
        elif any(kw in text for kw in ["price", "pricing", "plan", "cost", "subscription"]):
            return "pricing"
        elif any(kw in text for kw in ["bug", "fix", "issue", "error", "crash"]):
            return "bug"
        elif any(kw in text for kw in ["strategy", "acquisition", "partnership", "merger"]):
            return "strategy"
        else:
            return "feature"
    
    def _fallback_generate_tags(self, title: str, content: str) -> List[str]:
        """降级标签生成策略：使用关键词匹配"""
        text = (title + " " + content).lower()
        matched_tags = []
        
        tag_keywords = {
            "A/B Testing": ["a/b", "ab test", "experiment"],
            "Funnel": ["funnel", "conversion"],
            "Session Replay": ["session", "replay", "recording"],
            "AI Insights": ["ai", "insight", "intelligence"],
            "Data Warehouse": ["warehouse", "data lake", "storage"],
            "Real-time Analytics": ["real-time", "realtime", "live"],
            "User Segmentation": ["segment", "cohort", "group"],
            "Retention Analysis": ["retention", "churn"],
            "Cohort Analysis": ["cohort"],
            "Product Analytics": ["analytics", "analysis"]
        }
        
        for tag, keywords in tag_keywords.items():
            if any(kw in text for kw in keywords):
                matched_tags.append(tag)
                if len(matched_tags) >= 5:
                    break
        
        return matched_tags
    
    def _fallback_summary(self, content: str, max_length: int) -> str:
        """降级摘要策略：简单截断"""
        if len(content) <= max_length:
            return content
        
        # 在句子边界截断
        truncated = content[:max_length]
        last_period = truncated.rfind('.')
        last_question = truncated.rfind('?')
        last_exclamation = truncated.rfind('!')
        
        last_sentence_end = max(last_period, last_question, last_exclamation)
        
        if last_sentence_end > max_length * 0.7:  # 如果找到的句子边界不太远
            return truncated[:last_sentence_end + 1]
        else:
            return truncated[:max_length - 3] + "..."
    
    def _parse_trends(self, llm_response: str, updates: List[Dict]) -> List[Dict]:
        """解析 LLM 返回的趋势分析结果"""
        trends = []
        lines = llm_response.strip().split('\n')
        
        current_trend = None
        for line in lines:
            line = line.strip()
            if line.startswith('Trend:'):
                if current_trend:
                    trends.append(current_trend)
                current_trend = {
                    'trend_title': line.replace('Trend:', '').strip(),
                    'update_count': 0,
                    'products': set(),
                    'sample_updates': []
                }
            elif line.startswith('Updates:') and current_trend:
                # 解析更新编号
                numbers_str = line.replace('Updates:', '').strip()
                try:
                    numbers = [int(n.strip()) for n in numbers_str.split(',')]
                    for num in numbers:
                        if 1 <= num <= len(updates):
                            update = updates[num - 1]
                            current_trend['products'].add(update.get('product'))
                            if len(current_trend['sample_updates']) < 3:
                                current_trend['sample_updates'].append({
                                    'title': update.get('title'),
                                    'product': update.get('product')
                                })
                    current_trend['update_count'] = len(numbers)
                except:
                    pass
        
        if current_trend:
            trends.append(current_trend)
        
        # 转换 set 为 list
        for trend in trends:
            trend['products'] = list(trend['products'])
        
        # 按更新数量排序
        trends.sort(key=lambda x: x['update_count'], reverse=True)
        
        return trends[:10]
