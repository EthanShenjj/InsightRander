"""
使用 Playwright 采集 JS 渲染的页面
需要安装: pip install playwright && playwright install chromium
"""
from .base import BaseCollector
from datetime import datetime
import re

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Warning: Playwright not installed. Install with: pip install playwright && playwright install chromium")


class SensorsDataCollector(BaseCollector):
    """神策数据采集器 - 使用 RSS Feed"""
    
    def __init__(self):
        super().__init__('神策数据')
        self.rss_url = 'https://blog.csdn.net/sensorsdata/rss/list'
    
    def collect(self):
        """从 CSDN 博客 RSS 采集神策数据的文章"""
        try:
            import feedparser
            
            feed = feedparser.parse(self.rss_url)
            updates = []
            
            # 只采集最新的 15 条
            for entry in feed.entries[:15]:
                try:
                    title = entry.get('title', 'No Title')
                    content = entry.get('description', entry.get('summary', ''))
                    source_url = entry.get('link', self.rss_url)
                    
                    # 解析日期
                    if hasattr(entry, 'published_parsed'):
                        publish_time = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed'):
                        publish_time = datetime(*entry.updated_parsed[:6])
                    else:
                        publish_time = datetime.utcnow()
                    
                    # 判断内容类型
                    is_product_update = any(keyword in title.lower() 
                                          for keyword in ['产品', '功能', '发布', '更新', '升级'])
                    
                    updates.append(self.standardize_update(
                        title=title,
                        content=content,
                        source_type='blog' if not is_product_update else 'changelog',
                        source_url=source_url,
                        publish_time=publish_time,
                        raw_data={'product': '神策数据', 'type': 'feature' if is_product_update else 'blog'}
                    ))
                except Exception as e:
                    print(f"Error parsing SensorsData entry: {e}")
                    continue
            
            return updates
        except Exception as e:
            print(f"Error collecting SensorsData: {e}")
            return []


class MixpanelPlaywrightCollector(BaseCollector):
    """使用 Playwright 采集 Mixpanel Releases"""
    
    def __init__(self):
        super().__init__('Mixpanel')
        self.url = 'https://mixpanel.com/releases/'
    
    def collect(self):
        if not PLAYWRIGHT_AVAILABLE:
            print("Playwright not available, skipping Mixpanel collection")
            return []
        
        updates = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, timeout=10000)
                page = browser.new_page()
                page.goto(self.url, wait_until='domcontentloaded', timeout=15000)
                page.wait_for_timeout(2000)  # 等待 JS 渲染
                content = page.content()
                browser.close()
        except Exception as e:
            print(f"Error collecting Mixpanel with Playwright: {e}")
        
        return updates
    
    def _parse_date(self, date_str):
        if not date_str:
            return datetime.utcnow()
        
        formats = ['%B %d, %Y', '%Y-%m-%d', '%b %d, %Y', '%d %B %Y', '%m/%d/%Y']
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue
        return datetime.utcnow()


class AmplitudePlaywrightCollector(BaseCollector):
    """使用 Playwright 采集 Amplitude Product Updates"""
    
    def __init__(self):
        super().__init__('Amplitude')
        self.url = 'https://community.amplitude.com/product-updates'
    
    def collect(self):
        if not PLAYWRIGHT_AVAILABLE:
            print("Playwright not available, skipping Amplitude collection")
            return []
        
        updates = []
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(self.url, wait_until='networkidle', timeout=30000)
                
                # 等待内容加载
                page.wait_for_selector('body', timeout=10000)
                
                content = page.content()
                
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(content, 'html.parser')
                
                # 查找更新条目
                entries = soup.find_all(['article', 'div', 'li'], class_=re.compile(r'post|topic|update', re.I))
                
                for entry in entries[:15]:
                    try:
                        title_tag = entry.find(['h1', 'h2', 'h3', 'h4', 'a'])
                        if not title_tag:
                            continue
                        
                        title = title_tag.get_text(strip=True)
                        if not title or len(title) < 5:
                            continue
                        
                        # 提取日期
                        date_tag = entry.find(['time', 'span'], class_=re.compile(r'date|time|created', re.I))
                        publish_time = self._parse_date(date_tag.get_text(strip=True) if date_tag else None)
                        
                        # 提取内容
                        content_tag = entry.find(['p', 'div'], class_=re.compile(r'content|excerpt|summary', re.I))
                        content = content_tag.get_text(strip=True) if content_tag else title
                        
                        # 提取链接
                        link_tag = entry.find('a', href=True)
                        source_url = link_tag['href'] if link_tag else self.url
                        if not source_url.startswith('http'):
                            source_url = f"https://community.amplitude.com{source_url}"
                        
                        updates.append(self.standardize_update(
                            title=title,
                            content=content,
                            source_type='changelog',
                            source_url=source_url,
                            publish_time=publish_time,
                            raw_data={'product': 'Amplitude', 'type': 'feature'}
                        ))
                    except Exception as e:
                        print(f"Error parsing Amplitude entry: {e}")
                        continue
                
                browser.close()
        except Exception as e:
            print(f"Error collecting Amplitude with Playwright: {e}")
        
        return updates
    
    def _parse_date(self, date_str):
        if not date_str:
            return datetime.utcnow()
        
        formats = ['%B %d, %Y', '%Y-%m-%d', '%b %d, %Y', '%d %B %Y', '%m/%d/%Y']
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue
        return datetime.utcnow()
