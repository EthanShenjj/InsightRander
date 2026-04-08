import os
import time
import requests
from datetime import datetime
from typing import List, Dict, Optional
from .base import BaseCollector


class SocialMediaCollector(BaseCollector):
    """
    社交媒体数据采集器
    
    支持两种模式：
    - fast: 使用 Tavily API 快速洞察
    - deep: 使用 Apify API 深度抓取
    """
    
    def __init__(self, product_name: str, keywords: List[str], mode: str = 'fast'):
        """
        初始化社交媒体采集器
        
        Args:
            product_name: 产品名称
            keywords: 搜索关键词列表
            mode: 采集模式 ('fast' 或 'deep')
        """
        super().__init__(product_name)
        self.keywords = keywords
        self.mode = mode
        
        # 从环境变量加载 API 配置
        self.tavily_api_key = os.getenv('TAVILY_API_KEY')
        self.apify_api_key = os.getenv('APIFY_API_KEY')
        
        # API 端点
        self.tavily_url = "https://api.tavily.com/search"
        self.apify_url = "https://api.apify.com/v2/acts"
    
    def collect(self) -> List[Dict]:
        """
        执行社交媒体数据采集
        
        Returns:
            标准化的更新记录列表
        """
        all_updates = []
        
        for keyword in self.keywords:
            try:
                if self.mode == 'fast':
                    updates = self._collect_from_tavily(keyword)
                else:
                    updates = self._collect_from_apify(keyword)
                
                all_updates.extend(updates)
                print(f"[{self.product_name}] Collected {len(updates)} updates for keyword: {keyword}")
                
            except Exception as e:
                print(f"[{self.product_name}] Error collecting for keyword '{keyword}': {e}")
                continue
        
        return all_updates
    
    def _collect_from_tavily(self, keyword: str) -> List[Dict]:
        """
        使用 Tavily API 采集数据
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            标准化的更新记录列表
        """
        if not self.tavily_api_key:
            print(f"[{self.product_name}] TAVILY_API_KEY not configured, skipping Tavily collection")
            return []
        
        # 构建搜索查询
        query = f"{self.product_name} {keyword}"
        
        payload = {
            "api_key": self.tavily_api_key,
            "query": query,
            "search_depth": "basic",
            "include_raw_content": False,
            "max_results": 10
        }
        
        # 带重试的 API 调用
        response = self._call_api_with_retry(
            url=self.tavily_url,
            method='POST',
            json=payload,
            service_name='Tavily'
        )
        
        if not response:
            return []
        
        # 解析响应
        updates = []
        results = response.get('results', [])
        
        for item in results:
            try:
                # 解析发布时间
                publish_time = self._parse_date(item.get('published_date'))
                
                # 标准化更新记录
                update = self.standardize_update(
                    title=item.get('title', ''),
                    content=item.get('content', ''),
                    source_type='social',
                    source_url=item.get('url', ''),
                    publish_time=publish_time,
                    raw_data={
                        'source': 'tavily',
                        'keyword': keyword,
                        'score': item.get('score')
                    }
                )
                updates.append(update)
                
            except Exception as e:
                print(f"[{self.product_name}] Error parsing Tavily result: {e}")
                continue
        
        return updates
    
    def _collect_from_apify(self, keyword: str) -> List[Dict]:
        """
        使用 Apify API 采集数据
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            标准化的更新记录列表
        """
        if not self.apify_api_key:
            print(f"[{self.product_name}] APIFY_API_KEY not configured, skipping Apify collection")
            return []
        
        # 使用 web-scraper actor 进行深度抓取
        # 这里使用通用的 web-scraper，实际使用时可以配置特定的 actor
        actor_id = "apify/web-scraper"
        
        # 构建任务输入
        run_input = {
            "startUrls": [
                {"url": f"https://www.google.com/search?q={self.product_name}+{keyword}"}
            ],
            "linkSelector": "a[href]",
            "globPatterns": ["**/*"],
            "pageFunction": """
                async function pageFunction(context) {
                    const { request, log, jQuery } = context;
                    const $ = jQuery;
                    
                    const results = [];
                    $('div.g').each((i, el) => {
                        const title = $(el).find('h3').text();
                        const url = $(el).find('a').attr('href');
                        const snippet = $(el).find('.VwiC3b').text();
                        
                        if (title && url) {
                            results.push({
                                title,
                                url,
                                content: snippet,
                                published_date: new Date().toISOString()
                            });
                        }
                    });
                    
                    return results;
                }
            """,
            "maxPagesPerCrawl": 5
        }
        
        # 启动 Apify actor 运行
        run_url = f"{self.apify_url}/{actor_id}/runs?token={self.apify_api_key}"
        
        run_response = self._call_api_with_retry(
            url=run_url,
            method='POST',
            json=run_input,
            service_name='Apify'
        )
        
        if not run_response:
            return []
        
        # 获取运行 ID
        run_id = run_response.get('data', {}).get('id')
        if not run_id:
            print(f"[{self.product_name}] Failed to get Apify run ID")
            return []
        
        # 等待运行完成并获取结果
        results = self._wait_for_apify_results(actor_id, run_id)
        
        # 解析结果
        updates = []
        for item in results:
            try:
                publish_time = self._parse_date(item.get('published_date'))
                
                update = self.standardize_update(
                    title=item.get('title', ''),
                    content=item.get('content', ''),
                    source_type='social',
                    source_url=item.get('url', ''),
                    publish_time=publish_time,
                    raw_data={
                        'source': 'apify',
                        'keyword': keyword,
                        'actor_id': actor_id
                    }
                )
                updates.append(update)
                
            except Exception as e:
                print(f"[{self.product_name}] Error parsing Apify result: {e}")
                continue
        
        return updates
    
    def _wait_for_apify_results(self, actor_id: str, run_id: str, timeout: int = 300) -> List[Dict]:
        """
        等待 Apify 运行完成并获取结果
        
        Args:
            actor_id: Actor ID
            run_id: 运行 ID
            timeout: 超时时间（秒）
            
        Returns:
            结果列表
        """
        start_time = time.time()
        status_url = f"{self.apify_url}/{actor_id}/runs/{run_id}?token={self.apify_api_key}"
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(status_url, timeout=30)
                response.raise_for_status()
                
                data = response.json().get('data', {})
                status = data.get('status')
                
                if status in ['SUCCEEDED', 'FINISHED']:
                    # 获取结果
                    results_url = f"{self.apify_url}/{actor_id}/runs/{run_id}/results/items?token={self.apify_api_key}"
                    results_response = requests.get(results_url, timeout=30)
                    results_response.raise_for_status()
                    return results_response.json()
                
                elif status in ['FAILED', 'ABORTED', 'TIMED-OUT']:
                    print(f"[{self.product_name}] Apify run failed with status: {status}")
                    return []
                
                # 等待后重试
                time.sleep(5)
                
            except Exception as e:
                print(f"[{self.product_name}] Error checking Apify run status: {e}")
                time.sleep(5)
        
        print(f"[{self.product_name}] Apify run timed out after {timeout} seconds")
        return []
    
    def _call_api_with_retry(
        self, 
        url: str, 
        method: str = 'GET', 
        json: Optional[Dict] = None,
        service_name: str = 'API',
        max_retries: int = 3
    ) -> Optional[Dict]:
        """
        带重试机制的 API 调用（指数退避）
        
        Args:
            url: API URL
            method: HTTP 方法
            json: JSON 负载
            service_name: 服务名称（用于日志）
            max_retries: 最大重试次数
            
        Returns:
            API 响应数据，失败返回 None
        """
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                if method.upper() == 'POST':
                    response = requests.post(url, json=json, timeout=30)
                else:
                    response = requests.get(url, timeout=30)
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.Timeout:
                last_exception = Exception(f"{service_name} API timeout")
                wait_time = (2 ** attempt)  # 指数退避: 1s, 2s, 4s
                print(f"[{self.product_name}] {service_name} API timeout, retrying in {wait_time}s...")
                time.sleep(wait_time)
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code in [429, 502, 503, 504]:
                    # 可重试的错误
                    last_exception = e
                    wait_time = (2 ** attempt)
                    print(f"[{self.product_name}] {service_name} API error {e.response.status_code}, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    # 不可重试的错误
                    print(f"[{self.product_name}] {service_name} API error: {e}")
                    return None
                    
            except Exception as e:
                last_exception = e
                print(f"[{self.product_name}] {service_name} API error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        
        print(f"[{self.product_name}] {service_name} API failed after {max_retries} retries: {last_exception}")
        return None
    
    def _parse_date(self, date_str: Optional[str]) -> datetime:
        """
        解析日期字符串
        
        Args:
            date_str: 日期字符串
            
        Returns:
            datetime 对象，解析失败返回当前时间
        """
        if not date_str:
            return datetime.utcnow()
        
        # 尝试多种日期格式
        date_formats = [
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%d',
            '%a, %d %b %Y %H:%M:%S %Z',
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # 所有格式都失败，返回当前时间
        print(f"[{self.product_name}] Failed to parse date: {date_str}, using current time")
        return datetime.utcnow()