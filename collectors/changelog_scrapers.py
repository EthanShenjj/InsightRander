"""
专门针对各竞品 Changelog 页面的采集器
使用 requests + BeautifulSoup，如果页面是 JS 渲染的，需要使用 Playwright
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin
from .base import BaseCollector
import re


class PostHogChangelogCollector(BaseCollector):
    """PostHog Changelog 采集器"""
    
    def __init__(self):
        super().__init__('PostHog')
        # PostHog 使用 RSS feed 作为 changelog
        self.changelog_url = 'https://posthog.com/rss.xml'
        self.is_rss = True
    
    def collect(self):
        """
        PostHog 使用 RSS feed，包含 changelog 和 blog 内容
        """
        try:
            import feedparser
            
            feed = feedparser.parse(self.changelog_url)
            updates = []
            
            # 只采集最新的 15 条
            for entry in feed.entries[:15]:
                try:
                    title = entry.get('title', 'No Title')
                    content = entry.get('description', entry.get('summary', ''))
                    source_url = entry.get('link', self.changelog_url)
                    
                    # 解析日期
                    if hasattr(entry, 'published_parsed'):
                        publish_time = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed'):
                        publish_time = datetime(*entry.updated_parsed[:6])
                    else:
                        publish_time = datetime.utcnow()
                    
                    # 判断是否是 changelog 条目（通常包含特定关键词）
                    is_changelog = any(keyword in title.lower() or keyword in source_url.lower() 
                                     for keyword in ['changelog', 'release', 'update', 'feature'])
                    
                    updates.append(self.standardize_update(
                        title=title,
                        content=content,
                        source_type='changelog' if is_changelog else 'blog',
                        source_url=source_url,
                        publish_time=publish_time,
                        raw_data={'product': 'PostHog', 'type': 'feature'}
                    ))
                except Exception as e:
                    print(f"Error parsing PostHog entry: {e}")
                    continue
            
            return updates
        except Exception as e:
            print(f"Error collecting PostHog changelog: {e}")
            return []
    
    def _parse_date(self, date_str):
        """解析日期字符串"""
        if not date_str:
            return datetime.utcnow()
        
        # 尝试多种日期格式
        formats = [
            '%B %d, %Y',  # January 15, 2024
            '%Y-%m-%d',   # 2024-01-15
            '%b %d, %Y',  # Jan 15, 2024
            '%d %B %Y',   # 15 January 2024
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue
        
        return datetime.utcnow()


class MixpanelChangelogCollector(BaseCollector):
    """Mixpanel Changelog 采集器 - 通过爬取 docs.mixpanel.com/changelogs 实现"""
    
    def __init__(self):
        super().__init__('Mixpanel')
        self.index_url = 'https://docs.mixpanel.com/changelogs'
    
    def collect(self):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
            # 先用搜索引擎找最新的 changelog 条目
            import feedparser, requests
            from bs4 import BeautifulSoup
            from urllib.parse import urljoin
            
            # 直接请求 changelog 列表页
            response = requests.get(self.index_url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            updates = []
            # 找所有 changelog 链接
            links = soup.find_all('a', href=re.compile(r'/changelogs/\d{4}-\d{2}-\d{2}-'))
            seen_urls = set()
            
            for link in links[:15]:
                href = link.get('href', '')
                url = urljoin('https://docs.mixpanel.com', href)
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                
                try:
                    title = link.get_text(strip=True) or href.split('/')[-1].replace('-', ' ').title()
                    # 从 URL 中提取日期
                    date_match = re.search(r'/changelogs/(\d{4}-\d{2}-\d{2})-', href)
                    publish_time = datetime.strptime(date_match.group(1), '%Y-%m-%d') if date_match else datetime.utcnow()
                    
                    updates.append(self.standardize_update(
                        title=title,
                        content=title,
                        source_type='changelog',
                        source_url=url,
                        publish_time=publish_time,
                        raw_data={'product': 'Mixpanel', 'type': 'feature'}
                    ))
                except Exception as e:
                    continue
            
            # 如果列表页没有找到链接，用已知的 URL 格式直接抓取详情
            if not updates:
                updates = self._fetch_known_changelogs()
            
            return updates
        except Exception as e:
            print(f"Error collecting Mixpanel changelog: {e}")
            return self._fetch_known_changelogs()
    
    def _fetch_known_changelogs(self):
        """通过搜索已知的 changelog URL 格式来采集"""
        import requests
        from bs4 import BeautifulSoup
        
        # 已知的最新 changelog 条目（从搜索结果中获取）
        known_urls = [
            'https://docs.mixpanel.com/changelogs/2026-02-26-tls1011-deprecation',
            'https://docs.mixpanel.com/changelogs/2026-02-24-postgres-connector',
            'https://docs.mixpanel.com/changelogs/2026-01-26-decide-deprecation',
            'https://docs.mixpanel.com/changelogs/2025-10-13-feature-flagging',
            'https://docs.mixpanel.com/changelogs/2025-09-02-data-retention-update',
            'https://docs.mixpanel.com/changelogs/2025-08-18-growth-custom-session-replay',
            'https://docs.mixpanel.com/changelogs/2025-08-11-experimentation-reporting',
            'https://docs.mixpanel.com/changelogs/2025-02-10-b2b-company-analytics',
            'https://docs.mixpanel.com/changelogs/2024-02-13-new-funnels-retention',
        ]
        
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        updates = []
        
        for url in known_urls:
            try:
                resp = requests.get(url, headers=headers, timeout=8)
                if resp.status_code != 200:
                    continue
                soup = BeautifulSoup(resp.content, 'html.parser')
                
                # 提取标题
                title_tag = soup.find('h1') or soup.find('title')
                title = title_tag.get_text(strip=True).replace(' - Mixpanel Docs', '') if title_tag else url.split('/')[-1]
                
                # 提取内容
                content_tag = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|body'))
                content = content_tag.get_text(strip=True)[:500] if content_tag else title
                
                # 从 URL 提取日期
                date_match = re.search(r'/changelogs/(\d{4}-\d{2}-\d{2})-', url)
                publish_time = datetime.strptime(date_match.group(1), '%Y-%m-%d') if date_match else datetime.utcnow()
                
                updates.append(self.standardize_update(
                    title=title,
                    content=content,
                    source_type='changelog',
                    source_url=url,
                    publish_time=publish_time,
                    raw_data={'product': 'Mixpanel', 'type': 'feature'}
                ))
            except Exception as e:
                continue
        
        return updates
    
    def _parse_date(self, date_str):
        if not date_str:
            return datetime.utcnow()
        for fmt in ['%B %d, %Y', '%Y-%m-%d', '%b %d, %Y']:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue
        return datetime.utcnow()


class AmplitudeChangelogCollector(BaseCollector):
    """Amplitude Changelog 采集器 - 直接爬取 amplitude.com/platform-updates"""
    
    def __init__(self):
        super().__init__('Amplitude')
        self.url = 'https://amplitude.com/platform-updates'
    
    def collect(self):
        try:
            import requests
            from bs4 import BeautifulSoup
            
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
            response = requests.get(self.url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            updates = []
            
            # 提取页面中的所有段落内容
            # Amplitude platform-updates 页面结构：月份标题 + 内容描述
            body_text = soup.get_text(separator='\n')
            
            # 解析月份和内容块
            month_pattern = re.compile(
                r'(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+(\d{4})\s*\|?\s*([^\n]+)',
                re.IGNORECASE
            )
            
            month_map = {
                'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
                'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
            }
            
            matches = month_pattern.findall(body_text)
            seen_titles = set()
            
            for month_str, year_str, title in matches:
                title = title.strip()
                if not title or title in seen_titles or len(title) < 5:
                    continue
                seen_titles.add(title)
                
                try:
                    month = month_map.get(month_str.upper(), 1)
                    year = int(year_str)
                    publish_time = datetime(year, month, 1)
                    
                    updates.append(self.standardize_update(
                        title=title,
                        content=title,
                        source_type='changelog',
                        source_url=self.url,
                        publish_time=publish_time,
                        raw_data={'product': 'Amplitude', 'type': 'feature'}
                    ))
                except Exception:
                    continue
            
            return updates
        except Exception as e:
            print(f"Error collecting Amplitude changelog: {e}")
            return []
    
    def _parse_date(self, date_str):
        if not date_str:
            return datetime.utcnow()
        for fmt in ['%B %d, %Y', '%Y-%m-%d', '%b %d, %Y']:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue
        return datetime.utcnow()
