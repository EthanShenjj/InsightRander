import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin
from .base import BaseCollector

class ChangelogCollector(BaseCollector):
    def __init__(self, product_name, changelog_url, entry_selector, date_selector, title_selector, content_selector):
        """
        Generic BeautifulSoup-based changelog scraper.
        """
        super().__init__(product_name)
        self.changelog_url = changelog_url
        self.entry_selector = entry_selector
        self.date_selector = date_selector
        self.title_selector = title_selector
        self.content_selector = content_selector

    def collect(self):
        response = requests.get(self.changelog_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        entries = soup.select(self.entry_selector)
        updates = []
        
        for entry in entries:
            # Title
            title_tag = entry.select_one(self.title_selector)
            title = title_tag.get_text(strip=True) if title_tag else "No Title"
            
            # Content
            content_tag = entry.select_one(self.content_selector)
            content = content_tag.get_text(strip=True) if content_tag else "No Content"
            
            # Date (Simple parsing, can be improved)
            date_tag = entry.select_one(self.date_selector)
            date_str = date_tag.get_text(strip=True) if date_tag else None
            try:
                publish_time = datetime.strptime(date_str, '%B %d, %Y') if date_str else datetime.utcnow()
            except:
                publish_time = datetime.utcnow()
                
            # URL (Often the entry itself is an anchor or has one)
            source_url = self.changelog_url
            link_tag = entry.find('a', href=True)
            if link_tag:
                source_url = urljoin(self.changelog_url, link_tag['href'])
                
            updates.append(self.standardize_update(
                title=title,
                content=content,
                source_type='changelog',
                source_url=source_url,
                publish_time=publish_time
            ))
            
        return updates
