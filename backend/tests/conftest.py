"""
Test configuration and fixtures
"""
import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
import sys
import os
import json

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class MockProductUpdate:
    """Mock ProductUpdate with proper tags_list property"""
    def __init__(self):
        self.id = 'test-id-123'
        self.title = 'Test Title'
        self.content = 'Test Content'
        self._tags = None
        self.summary = None
        self.update_type = None
        self.source_type = 'blog'
        self.source_url = 'https://example.com/test'
        self.publish_time = datetime.utcnow()
    
    @property
    def tags(self):
        return self._tags
    
    @tags.setter
    def tags(self, value):
        self._tags = value
    
    @property
    def tags_list(self):
        """Get tags as a list"""
        if self._tags:
            try:
                return json.loads(self._tags)
            except:
                return []
        return []
    
    @tags_list.setter
    def tags_list(self, value):
        """Set tags from a list"""
        if value:
            self._tags = json.dumps(value)
        else:
            self._tags = None


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    return session


@pytest.fixture
def mock_llm_analyzer():
    """Mock LLM Analyzer"""
    analyzer = MagicMock()
    analyzer.classify_content = MagicMock(return_value='feature')
    analyzer.generate_tags = MagicMock(return_value=['AI Insights', 'Product Analytics'])
    analyzer.generate_summary = MagicMock(return_value='Test summary')
    return analyzer


@pytest.fixture
def sample_update():
    """Create a sample ProductUpdate for testing"""
    update = MockProductUpdate()
    update.id = 'test-id-123'
    update.title = 'New AI Feature Released'
    update.content = 'We are excited to announce a new AI-powered analytics feature that provides intelligent insights.'
    update.summary = None
    update.update_type = None
    update.source_type = 'blog'
    update.source_url = 'https://example.com/test'
    update.publish_time = datetime.utcnow()
    return update


@pytest.fixture
def sample_long_update():
    """Create a sample ProductUpdate with long content"""
    update = MockProductUpdate()
    update.id = 'test-id-456'
    update.title = 'Major Platform Update'
    # Content > 500 chars to trigger LLM summarization
    update.content = 'We are thrilled to announce a comprehensive platform update that brings numerous enhancements and new features. ' * 10
    update.summary = None
    update.update_type = 'feature'
    update.source_type = 'blog'
    update.source_url = 'https://example.com/long'
    update.publish_time = datetime.utcnow()
    return update