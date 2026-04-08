"""
专门针对各竞品 Changelog 页面的采集器
使用 requests + BeautifulSoup 进行数据采集
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
            response = self.request_with_retry(self.index_url, headers=headers)
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
    """Amplitude Changelog 采集器 - 爬取 amplitude.com/releases"""
    
    def __init__(self):
        super().__init__('Amplitude')
        self.url = 'https://amplitude.com/releases'
        self.extract_doc_links = True  # 是否提取文档链接
    
    def collect(self):
        try:
            import requests
            from bs4 import BeautifulSoup
            
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
            response = self.request_with_retry(self.url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            updates = []
            # 查找所有 release 链接
            links = soup.find_all('a', href=re.compile(r'/releases/[a-z0-9-]+'))
            seen_urls = set()
            
            for link in links[:20]:
                href = link.get('href', '')
                release_url = f"https://amplitude.com{href}" if href.startswith('/') else href
                
                if release_url in seen_urls or release_url == 'https://amplitude.com/releases':
                    continue
                seen_urls.add(release_url)
                
                try:
                    # 获取完整的链接文本，包含日期
                    full_text = link.get_text(strip=True)
                    if not full_text or len(full_text) < 5:
                        continue
                    
                    # 从文本中提取日期和标题
                    date_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*(\d+)', full_text)
                    
                    if date_match:
                        # 提取日期
                        date_text = date_match.group(0)
                        publish_time = self._parse_date(date_text)
                        
                        # 清理标题：移除日期和后面的分类标签
                        title = full_text
                        title = re.sub(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*\d+', '', title)
                        title = re.sub(r'(Data|Activation|Session Replay|Guides and Surveys|Analytics|Experiment)$', '', title)
                        title = title.strip()
                    else:
                        title = full_text
                        publish_time = datetime.utcnow()
                    
                    if not title or len(title) < 3:
                        continue
                    
                    # 决定使用哪个URL
                    source_url = release_url
                    doc_url = None
                    
                    # 如果启用了文档链接提取，尝试获取文档链接
                    if self.extract_doc_links:
                        doc_url = self._extract_doc_link(release_url, headers)
                        if doc_url:
                            source_url = doc_url
                        else:
                            # 如果没有找到文档链接，使用 release URL
                            # 保留 release URL 以便用户可以访问原始页面
                            source_url = release_url
                    
                    updates.append(self.standardize_update(
                        title=title,
                        content=title,
                        source_type='changelog',
                        source_url=source_url,
                        publish_time=publish_time,
                        raw_data={'product': 'Amplitude', 'type': 'feature', 'release_url': release_url, 'doc_url': doc_url}
                    ))
                except Exception as e:
                    continue
            
            return updates
        except Exception as e:
            print(f"Error collecting Amplitude changelog: {e}")
            return []
    
    def _extract_doc_link(self, release_url: str, headers: dict) -> str:
        """从 release 页面提取文档链接"""
        try:
            import requests
            from bs4 import BeautifulSoup
            
            response = requests.get(release_url, headers=headers, timeout=5)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 查找指向 /docs/ 的链接，但排除导航栏的通用链接
            doc_links = soup.find_all('a', href=re.compile(r'/docs/'))
            
            for doc_link in doc_links:
                href = doc_link.get('href', '')
                
                # 排除通用的文档首页链接（通常在导航栏）
                if 'siteLocation=nav' in href or href.endswith('/docs/') or href == '/docs':
                    continue
                
                # 排除外部链接到 docs.developers.amplitude.com 的通用链接
                if 'docs.developers.amplitude.com' in href and '?' in href:
                    continue
                
                # 找到了具体的文档页面链接
                if href.startswith('/'):
                    return f"https://amplitude.com{href}"
                elif href.startswith('http'):
                    return href
            
        except Exception as e:
            print(f"Failed to extract doc link from {release_url}: {e}")
        
        return None
    
    def _parse_date(self, date_str):
        if not date_str:
            return datetime.utcnow()
        
        # 解析 "Mar 17" 或 "Mar 17, 2026" 格式
        month_map = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        
        match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d+),?\s*(\d{4})?', date_str)
        if match:
            month_str, day, year = match.groups()
            month = month_map.get(month_str, 1)
            year = int(year) if year else datetime.utcnow().year
            day = int(day)
            return datetime(year, month, day)
        
        return datetime.utcnow()
