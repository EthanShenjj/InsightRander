import hashlib
import time
import random
import requests
from abc import ABC, abstractmethod
from datetime import datetime

class BaseCollector(ABC):
    def __init__(self, product_name):
        self.product_name = product_name
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
        ]

    @abstractmethod
    def collect(self):
        pass

    def request_with_retry(self, url, headers=None, retries=3, backoff_factor=1.5):
        """带有重试机制和随机 UA 的请求方法"""
        last_exception = None
        current_headers = headers or {}
        
        for i in range(retries):
            try:
                # 随机选择一个 User-Agent
                if 'User-Agent' not in current_headers:
                    current_headers['User-Agent'] = random.choice(self.user_agents)
                
                response = requests.get(url, headers=current_headers, timeout=15)
                response.raise_for_status()
                return response
            except Exception as e:
                last_exception = e
                wait_time = backoff_factor ** i
                print(f"[{self.product_name}] Request failed: {e}. Retrying in {wait_time:.2f}s...")
                time.sleep(wait_time)
        
        print(f"[{self.product_name}] All retries failed for {url}")
        raise last_exception

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
