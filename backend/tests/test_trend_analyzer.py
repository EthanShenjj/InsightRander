"""
Unit tests for TrendAnalyzer service

Tests cover:
- Trend analysis logic
- Minimum update threshold (5 updates)
- Trend group structure
- Trending tags statistics
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock, ANY
from datetime import datetime, timedelta
from services.trend_analyzer import TrendAnalyzer


class MockUpdate:
    """Mock ProductUpdate object"""
    def __init__(self, title, content, product, publish_time, tags_list=None):
        self.title = title
        self.content = content
        self.product = product
        self.publish_time = publish_time
        self._tags_list = tags_list or []
    
    @property
    def tags_list(self):
        return self._tags_list


class ComparableMock:
    """A mock that supports comparison with any value and SQLAlchemy column methods"""
    def __ge__(self, other):
        return self
    
    def __le__(self, other):
        return self
    
    def __eq__(self, other):
        return self
    
    def __ne__(self, other):
        return self
    
    def __lt__(self, other):
        return self
    
    def __gt__(self, other):
        return self
    
    def desc(self):
        return self
    
    def isnot(self, other):
        return self


class TestTrendAnalyzer:
    """Test suite for TrendAnalyzer"""
    
    def test_analyze_trends_success(self, mock_llm_analyzer):
        """Test successful trend analysis"""
        # Create mock updates
        mock_updates = []
        now = datetime.utcnow()
        for i in range(10):
            mock_updates.append(MockUpdate(
                title=f'Update {i}',
                content=f'Content {i}',
                product='PostHog' if i % 2 == 0 else 'Amplitude',
                publish_time=now - timedelta(days=i)
            ))
        
        # Mock LLM response
        mock_llm_analyzer.analyze_trends.return_value = [
            {
                'trend_title': 'AI Features',
                'update_count': 5,
                'products': ['PostHog', 'Amplitude'],
                'sample_updates': [{'title': 'Update 1', 'product': 'PostHog'}]
            }
        ]
        
        # Create a mock query that returns our updates
        mock_query = MagicMock()
        mock_query.all.return_value = mock_updates
        mock_query.order_by.return_value = mock_query
        
        with patch('services.trend_analyzer.ProductUpdate') as MockProductUpdate:
            # Make publish_time a comparable mock so the filter expression works
            MockProductUpdate.publish_time = ComparableMock()
            MockProductUpdate.query.filter = MagicMock(return_value=mock_query)
            
            analyzer = TrendAnalyzer(llm_analyzer=mock_llm_analyzer)
            result = analyzer.analyze_trends(days=30)
        
        assert len(result) == 1
        assert result[0]['trend_title'] == 'AI Features'
        assert result[0]['update_count'] == 5
        mock_llm_analyzer.analyze_trends.assert_called_once()
    
    def test_analyze_trends_below_threshold(self, mock_llm_analyzer):
        """Test that analysis returns empty list when updates < 5 (Requirement 5.7)"""
        # Create only 3 updates (below threshold)
        mock_updates = []
        now = datetime.utcnow()
        for i in range(3):
            mock_updates.append(MockUpdate(
                title=f'Update {i}',
                content=f'Content {i}',
                product='PostHog',
                publish_time=now - timedelta(days=i)
            ))
        
        mock_query = MagicMock()
        mock_query.all.return_value = mock_updates
        mock_query.order_by.return_value = mock_query
        
        with patch('services.trend_analyzer.ProductUpdate') as MockProductUpdate:
            MockProductUpdate.publish_time = ComparableMock()
            MockProductUpdate.query.filter = MagicMock(return_value=mock_query)
            
            analyzer = TrendAnalyzer(llm_analyzer=mock_llm_analyzer)
            result = analyzer.analyze_trends(days=30)
        
        assert result == []
        mock_llm_analyzer.analyze_trends.assert_not_called()
    
    def test_analyze_trends_exactly_5_updates(self, mock_llm_analyzer):
        """Test boundary case: exactly 5 updates (minimum threshold)"""
        mock_updates = []
        now = datetime.utcnow()
        for i in range(5):
            mock_updates.append(MockUpdate(
                title=f'Update {i}',
                content=f'Content {i}',
                product='PostHog',
                publish_time=now - timedelta(days=i)
            ))
        
        mock_query = MagicMock()
        mock_query.all.return_value = mock_updates
        mock_query.order_by.return_value = mock_query
        
        with patch('services.trend_analyzer.ProductUpdate') as MockProductUpdate:
            MockProductUpdate.publish_time = ComparableMock()
            MockProductUpdate.query.filter = MagicMock(return_value=mock_query)
            
            mock_llm_analyzer.analyze_trends.return_value = []
            
            analyzer = TrendAnalyzer(llm_analyzer=mock_llm_analyzer)
            result = analyzer.analyze_trends(days=30)
        
        # Should call LLM since we have exactly 5 updates
        mock_llm_analyzer.analyze_trends.assert_called_once()
    
    def test_analyze_trends_max_10_groups(self, mock_llm_analyzer):
        """Test that at most 10 trend groups are returned (Requirement 5.6)"""
        mock_updates = []
        now = datetime.utcnow()
        for i in range(20):
            mock_updates.append(MockUpdate(
                title=f'Update {i}',
                content=f'Content {i}',
                product='PostHog',
                publish_time=now - timedelta(days=i)
            ))
        
        mock_query = MagicMock()
        mock_query.all.return_value = mock_updates
        mock_query.order_by.return_value = mock_query
        
        with patch('services.trend_analyzer.ProductUpdate') as MockProductUpdate:
            MockProductUpdate.publish_time = ComparableMock()
            MockProductUpdate.query.filter = MagicMock(return_value=mock_query)
            
            # LLM returns 10 trends (already limited by LLMAnalyzer._parse_trends)
            mock_llm_analyzer.analyze_trends.return_value = [
                {'trend_title': f'Trend {i}', 'update_count': 20 - i, 'products': ['PostHog'], 'sample_updates': []}
                for i in range(10)
            ]
            
            analyzer = TrendAnalyzer(llm_analyzer=mock_llm_analyzer)
            result = analyzer.analyze_trends(days=30)
        
        # Should be limited to 10 (by LLMAnalyzer._parse_trends)
        assert len(result) == 10
    
    def test_analyze_trends_sorted_by_count(self, mock_llm_analyzer):
        """Test that trends are sorted by update count descending (Requirement 5.5)"""
        mock_updates = []
        now = datetime.utcnow()
        for i in range(10):
            mock_updates.append(MockUpdate(
                title=f'Update {i}',
                content=f'Content {i}',
                product='PostHog',
                publish_time=now - timedelta(days=i)
            ))
        
        mock_query = MagicMock()
        mock_query.all.return_value = mock_updates
        mock_query.order_by.return_value = mock_query
        
        with patch('services.trend_analyzer.ProductUpdate') as MockProductUpdate:
            MockProductUpdate.publish_time = ComparableMock()
            MockProductUpdate.query.filter = MagicMock(return_value=mock_query)
            
            # LLM returns sorted trends (already sorted by LLMAnalyzer._parse_trends)
            mock_llm_analyzer.analyze_trends.return_value = [
                {'trend_title': 'Trend B', 'update_count': 7, 'products': ['Amplitude'], 'sample_updates': []},
                {'trend_title': 'Trend C', 'update_count': 5, 'products': ['Mixpanel'], 'sample_updates': []},
                {'trend_title': 'Trend A', 'update_count': 3, 'products': ['PostHog'], 'sample_updates': []},
            ]
            
            analyzer = TrendAnalyzer(llm_analyzer=mock_llm_analyzer)
            result = analyzer.analyze_trends(days=30)
        
        # Should be sorted by update_count descending (by LLMAnalyzer._parse_trends)
        assert result[0]['update_count'] == 7
        assert result[1]['update_count'] == 5
        assert result[2]['update_count'] == 3
    
    def test_analyze_trends_custom_days(self, mock_llm_analyzer):
        """Test that custom days parameter is used correctly"""
        mock_updates = []
        now = datetime.utcnow()
        for i in range(10):
            mock_updates.append(MockUpdate(
                title=f'Update {i}',
                content=f'Content {i}',
                product='PostHog',
                publish_time=now - timedelta(days=i)
            ))
        
        mock_query = MagicMock()
        mock_query.all.return_value = mock_updates
        mock_query.order_by.return_value = mock_query
        
        with patch('services.trend_analyzer.ProductUpdate') as MockProductUpdate:
            MockProductUpdate.publish_time = ComparableMock()
            MockProductUpdate.query.filter = MagicMock(return_value=mock_query)
            
            mock_llm_analyzer.analyze_trends.return_value = []
            
            analyzer = TrendAnalyzer(llm_analyzer=mock_llm_analyzer)
            result = analyzer.analyze_trends(days=7)
        
        # Verify filter was called
        assert MockProductUpdate.query.filter.called
    
    def test_analyze_trends_exception_handling(self, mock_llm_analyzer):
        """Test that exceptions are handled gracefully"""
        with patch('services.trend_analyzer.ProductUpdate') as MockProductUpdate:
            MockProductUpdate.publish_time = ComparableMock()
            MockProductUpdate.query.filter.side_effect = Exception('Database error')
            
            analyzer = TrendAnalyzer(llm_analyzer=mock_llm_analyzer)
            result = analyzer.analyze_trends(days=30)
        
        assert result == []
    
    def test_get_trending_tags_success(self, mock_llm_analyzer):
        """Test successful trending tags retrieval"""
        # Create mock updates with tags
        mock_updates = []
        now = datetime.utcnow()
        for i in range(5):
            mock_updates.append(MockUpdate(
                title=f'Update {i}',
                content=f'Content {i}',
                product='PostHog' if i % 2 == 0 else 'Amplitude',
                publish_time=now - timedelta(days=i),
                tags_list=['AI Insights', 'Funnel'] if i % 2 == 0 else ['Funnel', 'Session Replay']
            ))
        
        mock_query = MagicMock()
        mock_query.all.return_value = mock_updates
        
        with patch('services.trend_analyzer.ProductUpdate') as MockProductUpdate:
            MockProductUpdate.publish_time = ComparableMock()
            MockProductUpdate.tags = ComparableMock()
            MockProductUpdate.query.filter = MagicMock(return_value=mock_query)
            
            analyzer = TrendAnalyzer(llm_analyzer=mock_llm_analyzer)
            result = analyzer.get_trending_tags(days=30)
        
        # Should have tag statistics
        assert len(result) > 0
        
        # Find 'Funnel' tag (appears in all updates)
        funnel_tag = next((t for t in result if t['tag'] == 'Funnel'), None)
        assert funnel_tag is not None
        assert funnel_tag['count'] == 5
    
    def test_get_trending_tags_sorted_by_count(self, mock_llm_analyzer):
        """Test that tags are sorted by count descending"""
        mock_updates = []
        now = datetime.utcnow()
        for i in range(5):
            mock_updates.append(MockUpdate(
                title=f'Update {i}',
                content=f'Content {i}',
                product='PostHog',
                publish_time=now - timedelta(days=i),
                tags_list=['AI Insights'] if i < 3 else ['Funnel']
            ))
        
        mock_query = MagicMock()
        mock_query.all.return_value = mock_updates
        
        with patch('services.trend_analyzer.ProductUpdate') as MockProductUpdate:
            MockProductUpdate.publish_time = ComparableMock()
            MockProductUpdate.tags = ComparableMock()
            MockProductUpdate.query.filter = MagicMock(return_value=mock_query)
            
            analyzer = TrendAnalyzer(llm_analyzer=mock_llm_analyzer)
            result = analyzer.get_trending_tags(days=30)
        
        # Should be sorted by count descending
        assert result[0]['count'] >= result[1]['count']
    
    def test_get_trending_tags_no_tags(self, mock_llm_analyzer):
        """Test handling when no tags exist"""
        mock_query = MagicMock()
        mock_query.all.return_value = []
        
        with patch('services.trend_analyzer.ProductUpdate') as MockProductUpdate:
            MockProductUpdate.publish_time = ComparableMock()
            MockProductUpdate.tags = ComparableMock()
            MockProductUpdate.query.filter = MagicMock(return_value=mock_query)
            
            analyzer = TrendAnalyzer(llm_analyzer=mock_llm_analyzer)
            result = analyzer.get_trending_tags(days=30)
        
        assert result == []
    
    def test_get_trending_tags_products_list(self, mock_llm_analyzer):
        """Test that products list is correctly populated for each tag"""
        mock_updates = []
        now = datetime.utcnow()
        for i in range(3):
            mock_updates.append(MockUpdate(
                title=f'Update {i}',
                content=f'Content {i}',
                product=['PostHog', 'Amplitude', 'Mixpanel'][i],
                publish_time=now - timedelta(days=i),
                tags_list=['AI Insights']
            ))
        
        mock_query = MagicMock()
        mock_query.all.return_value = mock_updates
        
        with patch('services.trend_analyzer.ProductUpdate') as MockProductUpdate:
            MockProductUpdate.publish_time = ComparableMock()
            MockProductUpdate.tags = ComparableMock()
            MockProductUpdate.query.filter = MagicMock(return_value=mock_query)
            
            analyzer = TrendAnalyzer(llm_analyzer=mock_llm_analyzer)
            result = analyzer.get_trending_tags(days=30)
        
        # Should have all three products
        ai_tag = result[0]
        assert ai_tag['tag'] == 'AI Insights'
        assert set(ai_tag['products']) == {'PostHog', 'Amplitude', 'Mixpanel'}
    
    def test_get_trending_tags_exception_handling(self, mock_llm_analyzer):
        """Test that exceptions in get_trending_tags are handled gracefully"""
        with patch('services.trend_analyzer.ProductUpdate') as MockProductUpdate:
            MockProductUpdate.publish_time = ComparableMock()
            MockProductUpdate.tags = ComparableMock()
            MockProductUpdate.query.filter.side_effect = Exception('Database error')
            
            analyzer = TrendAnalyzer(llm_analyzer=mock_llm_analyzer)
            result = analyzer.get_trending_tags(days=30)
        
        assert result == []
    
    def test_analyze_trends_empty_updates(self, mock_llm_analyzer):
        """Test handling when no updates exist"""
        mock_query = MagicMock()
        mock_query.all.return_value = []
        mock_query.order_by.return_value = mock_query
        
        with patch('services.trend_analyzer.ProductUpdate') as MockProductUpdate:
            MockProductUpdate.publish_time = ComparableMock()
            MockProductUpdate.query.filter = MagicMock(return_value=mock_query)
            
            analyzer = TrendAnalyzer(llm_analyzer=mock_llm_analyzer)
            result = analyzer.analyze_trends(days=30)
        
        assert result == []
        mock_llm_analyzer.analyze_trends.assert_not_called()
    
    def test_analyze_trends_llm_failure(self, mock_llm_analyzer):
        """Test handling when LLM call fails"""
        mock_updates = []
        now = datetime.utcnow()
        for i in range(10):
            mock_updates.append(MockUpdate(
                title=f'Update {i}',
                content=f'Content {i}',
                product='PostHog',
                publish_time=now - timedelta(days=i)
            ))
        
        mock_query = MagicMock()
        mock_query.all.return_value = mock_updates
        mock_query.order_by.return_value = mock_query
        
        with patch('services.trend_analyzer.ProductUpdate') as MockProductUpdate:
            MockProductUpdate.publish_time = ComparableMock()
            MockProductUpdate.query.filter = MagicMock(return_value=mock_query)
            
            mock_llm_analyzer.analyze_trends.side_effect = Exception('LLM error')
            
            analyzer = TrendAnalyzer(llm_analyzer=mock_llm_analyzer)
            result = analyzer.analyze_trends(days=30)
        
        assert result == []
    
    def test_analyze_trends_data_preparation(self, mock_llm_analyzer):
        """Test that data is correctly prepared for LLM"""
        mock_updates = []
        now = datetime.utcnow()
        for i in range(5):
            mock_updates.append(MockUpdate(
                title=f'Title {i}',
                content=f'Content {i}',
                product=f'Product {i}',
                publish_time=now - timedelta(days=i)
            ))
        
        mock_query = MagicMock()
        mock_query.all.return_value = mock_updates
        mock_query.order_by.return_value = mock_query
        
        with patch('services.trend_analyzer.ProductUpdate') as MockProductUpdate:
            MockProductUpdate.publish_time = ComparableMock()
            MockProductUpdate.query.filter = MagicMock(return_value=mock_query)
            
            mock_llm_analyzer.analyze_trends.return_value = []
            
            analyzer = TrendAnalyzer(llm_analyzer=mock_llm_analyzer)
            analyzer.analyze_trends(days=30)
        
        # Verify LLM was called with correct data structure
        call_args = mock_llm_analyzer.analyze_trends.call_args[0][0]
        assert len(call_args) == 5
        assert call_args[0]['title'] == 'Title 0'
        assert call_args[0]['product'] == 'Product 0'
    
    def test_analyze_trends_with_null_content(self, mock_llm_analyzer):
        """Test handling of updates with null content"""
        mock_updates = []
        now = datetime.utcnow()
        for i in range(5):
            mock_updates.append(MockUpdate(
                title=f'Update {i}',
                content=None if i % 2 == 0 else f'Content {i}',
                product='PostHog',
                publish_time=now - timedelta(days=i)
            ))
        
        mock_query = MagicMock()
        mock_query.all.return_value = mock_updates
        mock_query.order_by.return_value = mock_query
        
        with patch('services.trend_analyzer.ProductUpdate') as MockProductUpdate:
            MockProductUpdate.publish_time = ComparableMock()
            MockProductUpdate.query.filter = MagicMock(return_value=mock_query)
            
            mock_llm_analyzer.analyze_trends.return_value = []
            
            analyzer = TrendAnalyzer(llm_analyzer=mock_llm_analyzer)
            analyzer.analyze_trends(days=30)
        
        # Verify null content is handled (converted to empty string)
        call_args = mock_llm_analyzer.analyze_trends.call_args[0][0]
        assert call_args[0]['content'] == ""
        assert call_args[1]['content'] == "Content 1"