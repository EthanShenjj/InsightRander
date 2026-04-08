"""
神策数据采集器
使用 requests + JSON 解析采集官方博客
"""
from .base import BaseCollector
from datetime import datetime
import re
import json


class SensorsDataCollector(BaseCollector):
    """神策数据采集器 - 爬取官方博客企业动态"""
    
    def __init__(self):
        super().__init__('神策数据')
        self.url = 'https://www.sensorsdata.cn/blog/tag/news'
    
    def collect(self):
        """从神策官方博客采集企业动态"""
        try:
            import requests
            
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
            response = requests.get(self.url, headers=headers, timeout=10)
            
            # 从页面中提取 __NEXT_DATA__ JSON 数据
            html_content = response.text
            
            # 查找 <script id="__NEXT_DATA__" type="application/json"> 标签
            json_match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html_content, re.DOTALL)
            
            if not json_match:
                print("未找到 __NEXT_DATA__ JSON 数据")
                return []
            
            # 解析 JSON 数据
            next_data = json.loads(json_match.group(1))
            
            # 提取文章列表
            articles_data = next_data.get('props', {}).get('pageProps', {}).get('TagDataList', {}).get('result', {}).get('data', [])
            
            if not articles_data:
                print("未找到文章数据")
                return []
            
            updates = []
            for article in articles_data[:20]:  # 取前20篇最新文章
                try:
                    title = article.get('title', '').strip()
                    slug = article.get('slug', '')
                    published_at = article.get('publishedAt', '')
                    
                    if not title or not slug:
                        continue
                    
                    # 构建文章URL
                    url = f"https://www.sensorsdata.cn/blog/{slug}"
                    
                    # 解析发布时间
                    publish_time = self._parse_datetime(published_at)
                    
                    updates.append(self.standardize_update(
                        title=title,
                        content=title,
                        source_type='blog',
                        source_url=url,
                        publish_time=publish_time,
                        raw_data={
                            'product': '神策数据',
                            'type': 'news',
                            'author': article.get('authorName', ''),
                            'keywords': article.get('metaKeywords', '')
                        }
                    ))
                except Exception as e:
                    print(f"Error parsing SensorsData article: {e}")
                    continue
            
            print(f"成功采集到 {len(updates)} 篇神策数据文章")
            return updates
            
        except Exception as e:
            print(f"Error collecting SensorsData: {e}")
            return []
    
    def _parse_datetime(self, datetime_str: str) -> datetime:
        """解析日期时间字符串"""
        try:
            # 格式: "2026-03-31 17:11:25"
            return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        except:
            return datetime.utcnow()

