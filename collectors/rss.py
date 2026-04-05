import feedparser
from datetime import datetime
from .base import BaseCollector

class RSSCollector(BaseCollector):
    def __init__(self, product_name, rss_url):
        super().__init__(product_name)
        self.rss_url = rss_url

    def collect(self):
        feed = feedparser.parse(self.rss_url)
        updates = []
        for entry in feed.entries:
            # RSS date parsing varies, so handle common formats
            published = None
            if hasattr(entry, 'published_parsed'):
                published = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed'):
                published = datetime(*entry.updated_parsed[:6])
            else:
                published = datetime.utcnow()

            title = entry.get('title', 'No Title')
            content = entry.get('description', entry.get('summary', 'No Description'))
            source_url = entry.get('link', '')

            updates.append(self.standardize_update(
                title=title,
                content=content,
                source_type='blog',
                source_url=source_url,
                publish_time=published,
                raw_data=entry
            ))
        return updates
