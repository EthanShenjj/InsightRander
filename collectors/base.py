import hashlib
from abc import ABC, abstractmethod

class BaseCollector(ABC):
    def __init__(self, product_name):
        self.product_name = product_name

    @abstractmethod
    def collect(self):
        """
        Should return a list of dictionaries in the standardized format.
        """
        pass

    def generate_content_hash(self, content):
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def standardize_update(self, title, content, source_type, source_url, publish_time, raw_data=None):
        return {
            "product": self.product_name,
            "title": title,
            "content": content,
            "source_type": source_type,
            "source_url": source_url,
            "publish_time": publish_time,
            "content_hash": self.generate_content_hash(f"{title}{content}"),
            "raw_data": raw_data or {}
        }
