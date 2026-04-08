"""
Unit tests for ReportGenerator service

Tests cover:
- Weekly report generation
- Empty report handling (Requirement 6.7)
- Most active product identification (Requirement 6.5)
- Trending categories identification (Requirement 6.6)
- Comparison matrix generation
- Leader identification (Requirement 7.5)
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, timedelta
from services.report_generator import ReportGenerator


class MockUpdate:
    """Mock ProductUpdate object"""
    def __init__(self, title, content, product, publish_time, update_type=None, tags_list=None, summary=None):
        self.title = title
        self.content = content
        self.product = product
        self.publish_time = publish_time
        self.update_type = update_type
        self._tags_list = tags_list or []
        self.summary = summary
    
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


class TestReportGenerator:
    """Test suite for ReportGenerator"""
    
    def test_generate_weekly_report_success(self, mock_llm_analyzer):
        """Test successful weekly report generation"""
        # Create mock updates
        mock_updates = []
        now = datetime.utcnow()
        for i in range(10):
            mock_updates.append(MockUpdate(
                title=f'Update {i}',
                content=f'Content {i}',
                product='PostHog' if i % 2 == 0 else 'Amplitude',
                publish_time=now - timedelta(days=i),
                update_type='feature' if i % 3 == 0 else 'bug',
                tags_list=['AI Insights'] if i % 2 == 0 else ['Funnel']
            ))
        
        # Create a mock query that returns our updates
        mock_query = MagicMock()
        mock_query.all.return_value = mock_updates
        mock_query.order_by.return_value = mock_query
        
        with patch('services.report_generator.ProductUpdate') as MockProductUpdate:
            MockProductUpdate.publish_time = ComparableMock()
            MockProductUpdate.query.filter = MagicMock(return_value=mock_query)
            
            generator = ReportGenerator(llm_analyzer=mock_llm_analyzer)
            result = generator.generate_weekly_report()
        
        assert 'period' in result
        assert result['total_updates'] == 10
        assert len(result['highlights']) == 5
        assert 'stats_by_product' in result
        assert 'stats_by_type' in result
        assert result['most_active_product'] is not None
        assert len(result['trending_categories']) > 0
    
    def test_generate_weekly_report_empty(self, mock_llm_analyzer):
        """Test that empty report is returned when no updates in past 7 days (Requirement 6.7)"""
        mock_query = MagicMock()
        mock_query.all.return_value = []
        mock_query.order_by.return_value = mock_query
        
        with patch('services.report_generator.ProductUpdate') as MockProductUpdate:
            MockProductUpdate.publish_time = ComparableMock()
            MockProductUpdate.query.filter = MagicMock(return_value=mock_query)
            
            generator = ReportGenerator(llm_analyzer=mock_llm_analyzer)
            result = generator.generate_weekly_report()
        
        assert result['total_updates'] == 0
        assert result['message'] == "No updates in the past 7 days"
        assert result['highlights'] == []
        assert result['most_active_product'] is None
    
    def test_generate_weekly_report_most_active_product(self, mock_llm_analyzer):
        """Test that most active product is correctly identified (Requirement 6.5)"""
        mock_updates = []
        now = datetime.utcnow()
        # PostHog has 7 updates, Amplitude has 3
        for i in range(7):
            mock_updates.append(MockUpdate(
                title=f'PostHog Update {i}',
                content=f'Content {i}',
                product='PostHog',
                publish_time=now - timedelta(days=i),
                update_type='feature'
            ))
        for i in range(3):
            mock_updates.append(MockUpdate(
                title=f'Amplitude Update {i}',
                content=f'Content {i}',
                product='Amplitude',
                publish_time=now - timedelta(days=i),
                update_type='feature'
            ))
        
        mock_query = MagicMock()
        mock_query.all.return_value = mock_updates
        mock_query.order_by.return_value = mock_query
        
        with patch('services.report_generator.ProductUpdate') as MockProductUpdate:
            MockProductUpdate.publish_time = ComparableMock()
            MockProductUpdate.query.filter = MagicMock(return_value=mock_query)
            
            generator = ReportGenerator(llm_analyzer=mock_llm_analyzer)
            result = generator.generate_weekly_report()
        
        assert result['most_active_product'] == 'PostHog'
        assert result['stats_by_product']['PostHog']['count'] == 7
        assert result['stats_by_product']['Amplitude']['count'] == 3
    
    def test_generate_weekly_report_trending_categories(self, mock_llm_analyzer):
        """Test that trending categories are correctly identified (Requirement 6.6)"""
        mock_updates = []
        now = datetime.utcnow()
        # feature: 5, bug: 3, ai: 2
        for i in range(5):
            mock_updates.append(MockUpdate(
                title=f'Feature {i}',
                content=f'Content {i}',
                product='PostHog',
                publish_time=now - timedelta(days=i),
                update_type='feature'
            ))
        for i in range(3):
            mock_updates.append(MockUpdate(
                title=f'Bug {i}',
                content=f'Content {i}',
                product='PostHog',
                publish_time=now - timedelta(days=i),
                update_type='bug'
            ))
        for i in range(2):
            mock_updates.append(MockUpdate(
                title=f'AI {i}',
                content=f'Content {i}',
                product='PostHog',
                publish_time=now - timedelta(days=i),
                update_type='ai'
            ))
        
        mock_query = MagicMock()
        mock_query.all.return_value = mock_updates
        mock_query.order_by.return_value = mock_query
        
        with patch('services.report_generator.ProductUpdate') as MockProductUpdate:
            MockProductUpdate.publish_time = ComparableMock()
            MockProductUpdate.query.filter = MagicMock(return_value=mock_query)
            
            generator = ReportGenerator(llm_analyzer=mock_llm_analyzer)
            result = generator.generate_weekly_report()
        
        # Should be sorted by count descending
        assert result['trending_categories'][0]['category'] == 'feature'
        assert result['trending_categories'][0]['count'] == 5
        assert result['trending_categories'][1]['category'] == 'bug'
        assert result['trending_categories'][1]['count'] == 3
    
    def test_generate_weekly_report_stats_by_product(self, mock_llm_analyzer):
        """Test that stats are correctly grouped by product (Requirement 6.4)"""
        mock_updates = []
        now = datetime.utcnow()
        for i in range(3):
            mock_updates.append(MockUpdate(
                title=f'PostHog Feature {i}',
                content=f'Content {i}',
                product='PostHog',
                publish_time=now - timedelta(days=i),
                update_type='feature'
            ))
            mock_updates.append(MockUpdate(
                title=f'PostHog Bug {i}',
                content=f'Content {i}',
                product='PostHog',
                publish_time=now - timedelta(days=i),
                update_type='bug'
            ))
        
        mock_query = MagicMock()
        mock_query.all.return_value = mock_updates
        mock_query.order_by.return_value = mock_query
        
        with patch('services.report_generator.ProductUpdate') as MockProductUpdate:
            MockProductUpdate.publish_time = ComparableMock()
            MockProductUpdate.query.filter = MagicMock(return_value=mock_query)
            
            generator = ReportGenerator(llm_analyzer=mock_llm_analyzer)
            result = generator.generate_weekly_report()
        
        assert 'PostHog' in result['stats_by_product']
        assert result['stats_by_product']['PostHog']['count'] == 6
        assert result['stats_by_product']['PostHog']['types']['feature'] == 3
        assert result['stats_by_product']['PostHog']['types']['bug'] == 3
    
    def test_generate_weekly_report_competitor_comparison(self, mock_llm_analyzer):
        """Test that competitor comparison is included in weekly report (Requirement 6.3)"""
        mock_updates = []
        now = datetime.utcnow()
        for i in range(5):
            mock_updates.append(MockUpdate(
                title=f'PostHog Update {i}',
                content=f'Content {i}',
                product='PostHog',
                publish_time=now - timedelta(days=i),
                update_type='feature',
                tags_list=['AI Insights', 'Funnel']
            ))
        for i in range(3):
            mock_updates.append(MockUpdate(
                title=f'Amplitude Update {i}',
                content=f'Content {i}',
                product='Amplitude',
                publish_time=now - timedelta(days=i),
                update_type='feature',
                tags_list=['Funnel', 'Session Replay']
            ))
        
        mock_query = MagicMock()
        mock_query.all.return_value = mock_updates
        mock_query.order_by.return_value = mock_query
        
        with patch('services.report_generator.ProductUpdate') as MockProductUpdate:
            MockProductUpdate.publish_time = ComparableMock()
            MockProductUpdate.query.filter = MagicMock(return_value=mock_query)
            
            generator = ReportGenerator(llm_analyzer=mock_llm_analyzer)
            result = generator.generate_weekly_report()
        
        assert 'competitor_comparison' in result
        assert 'product_counts' in result['competitor_comparison']
        assert result['competitor_comparison']['product_counts']['PostHog'] == 5
        assert result['competitor_comparison']['product_counts']['Amplitude'] == 3
    
    def test_generate_weekly_report_trend_insights(self, mock_llm_analyzer):
        """Test that trend insights are included in weekly report (Requirement 6.3)"""
        mock_updates = []
        now = datetime.utcnow()
        for i in range(5):
            mock_updates.append(MockUpdate(
                title=f'Update {i}',
                content=f'Content {i}',
                product='PostHog',
                publish_time=now - timedelta(days=i),
                update_type='feature',
                tags_list=['AI Insights', 'Funnel']
            ))
        
        mock_query = MagicMock()
        mock_query.all.return_value = mock_updates
        mock_query.order_by.return_value = mock_query
        
        with patch('services.report_generator.ProductUpdate') as MockProductUpdate:
            MockProductUpdate.publish_time = ComparableMock()
            MockProductUpdate.query.filter = MagicMock(return_value=mock_query)
            
            generator = ReportGenerator(llm_analyzer=mock_llm_analyzer)
            result = generator.generate_weekly_report()
        
        assert 'trend_insights' in result
        assert len(result['trend_insights']) > 0
        # Check that insights contain expected fields
        insight = result['trend_insights'][0]
        assert 'tag' in insight
        assert 'count' in insight
        assert 'products' in insight
    
    def test_generate_comparison_matrix_success(self, mock_llm_analyzer):
        """Test successful comparison matrix generation"""
        mock_updates = []
        now = datetime.utcnow()
        for i in range(5):
            mock_updates.append(MockUpdate(
                title=f'PostHog Update {i}',
                content=f'Content {i}',
                product='PostHog',
                publish_time=now - timedelta(days=i),
                tags_list=['AI Insights', 'Funnel']
            ))
        for i in range(3):
            mock_updates.append(MockUpdate(
                title=f'Amplitude Update {i}',
                content=f'Content {i}',
                product='Amplitude',
                publish_time=now - timedelta(days=i),
                tags_list=['Funnel', 'Session Replay']
            ))
        
        mock_query = MagicMock()
        mock_query.all.return_value = mock_updates
        
        with patch('services.report_generator.ProductUpdate') as MockProductUpdate:
            MockProductUpdate.tags = ComparableMock()
            MockProductUpdate.query.filter = MagicMock(return_value=mock_query)
            
            generator = ReportGenerator(llm_analyzer=mock_llm_analyzer)
            result = generator.generate_comparison_matrix()
        
        assert 'matrix' in result
        assert 'leaders' in result
        assert 'all_tags' in result
        assert 'summary' in result
        
        # Check matrix structure
        assert 'PostHog' in result['matrix']
        assert 'Amplitude' in result['matrix']
        assert result['matrix']['PostHog']['AI Insights'] == 5
        assert result['matrix']['PostHog']['Funnel'] == 5
        assert result['matrix']['Amplitude']['Funnel'] == 3
        assert result['matrix']['Amplitude']['Session Replay'] == 3
    
    def test_generate_comparison_matrix_leaders(self, mock_llm_analyzer):
        """Test that leaders are correctly identified (Requirement 7.5)"""
        mock_updates = []
        now = datetime.utcnow()
        # PostHog leads in AI Insights (5 vs 2)
        for i in range(5):
            mock_updates.append(MockUpdate(
                title=f'PostHog AI {i}',
                content=f'Content {i}',
                product='PostHog',
                publish_time=now - timedelta(days=i),
                tags_list=['AI Insights']
            ))
        for i in range(2):
            mock_updates.append(MockUpdate(
                title=f'Amplitude AI {i}',
                content=f'Content {i}',
                product='Amplitude',
                publish_time=now - timedelta(days=i),
                tags_list=['AI Insights']
            ))
        # Amplitude leads in Funnel (4 vs 1)
        for i in range(1):
            mock_updates.append(MockUpdate(
                title=f'PostHog Funnel {i}',
                content=f'Content {i}',
                product='PostHog',
                publish_time=now - timedelta(days=i),
                tags_list=['Funnel']
            ))
        for i in range(4):
            mock_updates.append(MockUpdate(
                title=f'Amplitude Funnel {i}',
                content=f'Content {i}',
                product='Amplitude',
                publish_time=now - timedelta(days=i),
                tags_list=['Funnel']
            ))
        
        mock_query = MagicMock()
        mock_query.all.return_value = mock_updates
        
        with patch('services.report_generator.ProductUpdate') as MockProductUpdate:
            MockProductUpdate.tags = ComparableMock()
            MockProductUpdate.query.filter = MagicMock(return_value=mock_query)
            
            generator = ReportGenerator(llm_analyzer=mock_llm_analyzer)
            result = generator.generate_comparison_matrix()
        
        # Check leaders format: {tag: product}
        assert result['leaders']['AI Insights'] == 'PostHog'
        assert result['leaders']['Funnel'] == 'Amplitude'
    
    def test_generate_comparison_matrix_empty(self, mock_llm_analyzer):
        """Test that empty matrix is returned when no tagged updates"""
        mock_query = MagicMock()
        mock_query.all.return_value = []
        
        with patch('services.report_generator.ProductUpdate') as MockProductUpdate:
            MockProductUpdate.tags = ComparableMock()
            MockProductUpdate.query.filter = MagicMock(return_value=mock_query)
            
            generator = ReportGenerator(llm_analyzer=mock_llm_analyzer)
            result = generator.generate_comparison_matrix()
        
        assert result['matrix'] == {}
        assert result['leaders'] == {}
        assert result['all_tags'] == []
    
    def test_generate_comparison_matrix_summary(self, mock_llm_analyzer):
        """Test that summary is correctly generated"""
        mock_updates = []
        now = datetime.utcnow()
        for i in range(5):
            mock_updates.append(MockUpdate(
                title=f'PostHog Update {i}',
                content=f'Content {i}',
                product='PostHog',
                publish_time=now - timedelta(days=i),
                tags_list=['AI Insights']
            ))
        
        mock_query = MagicMock()
        mock_query.all.return_value = mock_updates
        
        with patch('services.report_generator.ProductUpdate') as MockProductUpdate:
            MockProductUpdate.tags = ComparableMock()
            MockProductUpdate.query.filter = MagicMock(return_value=mock_query)
            
            generator = ReportGenerator(llm_analyzer=mock_llm_analyzer)
            result = generator.generate_comparison_matrix()
        
        assert len(result['summary']) > 0
        assert 'PostHog leads in AI Insights' in result['summary'][0]
    
    def test_generate_weekly_report_exception_handling(self, mock_llm_analyzer):
        """Test that exceptions are handled gracefully in weekly report"""
        with patch('services.report_generator.ProductUpdate') as MockProductUpdate:
            MockProductUpdate.publish_time = ComparableMock()
            MockProductUpdate.query.filter.side_effect = Exception('Database error')
            
            generator = ReportGenerator(llm_analyzer=mock_llm_analyzer)
            result = generator.generate_weekly_report()
        
        assert 'error' in result
        assert result['error'] == 'Database error'
    
    def test_generate_comparison_matrix_exception_handling(self, mock_llm_analyzer):
        """Test that exceptions are handled gracefully in comparison matrix"""
        with patch('services.report_generator.ProductUpdate') as MockProductUpdate:
            MockProductUpdate.tags = ComparableMock()
            MockProductUpdate.query.filter.side_effect = Exception('Database error')
            
            generator = ReportGenerator(llm_analyzer=mock_llm_analyzer)
            result = generator.generate_comparison_matrix()
        
        assert 'error' in result
        assert result['matrix'] == {}
        assert result['leaders'] == {}
    
    def test_generate_weekly_report_highlights_limit(self, mock_llm_analyzer):
        """Test that highlights are limited to 5 items"""
        mock_updates = []
        now = datetime.utcnow()
        for i in range(20):
            mock_updates.append(MockUpdate(
                title=f'Update {i}',
                content=f'Content {i}',
                product='PostHog',
                publish_time=now - timedelta(days=i),
                update_type='feature'
            ))
        
        mock_query = MagicMock()
        mock_query.all.return_value = mock_updates
        mock_query.order_by.return_value = mock_query
        
        with patch('services.report_generator.ProductUpdate') as MockProductUpdate:
            MockProductUpdate.publish_time = ComparableMock()
            MockProductUpdate.query.filter = MagicMock(return_value=mock_query)
            
            generator = ReportGenerator(llm_analyzer=mock_llm_analyzer)
            result = generator.generate_weekly_report()
        
        assert len(result['highlights']) == 5
    
    def test_generate_weekly_report_with_null_update_type(self, mock_llm_analyzer):
        """Test handling of updates with null update_type"""
        mock_updates = []
        now = datetime.utcnow()
        for i in range(5):
            mock_updates.append(MockUpdate(
                title=f'Update {i}',
                content=f'Content {i}',
                product='PostHog',
                publish_time=now - timedelta(days=i),
                update_type=None  # Null update_type
            ))
        
        mock_query = MagicMock()
        mock_query.all.return_value = mock_updates
        mock_query.order_by.return_value = mock_query
        
        with patch('services.report_generator.ProductUpdate') as MockProductUpdate:
            MockProductUpdate.publish_time = ComparableMock()
            MockProductUpdate.query.filter = MagicMock(return_value=mock_query)
            
            generator = ReportGenerator(llm_analyzer=mock_llm_analyzer)
            result = generator.generate_weekly_report()
        
        # Null update_type should be treated as 'unknown'
        assert 'unknown' in result['stats_by_type']
    
    def test_generate_comparison_matrix_all_tags_included(self, mock_llm_analyzer):
        """Test that all unique tags are included in all_tags list"""
        mock_updates = []
        now = datetime.utcnow()
        for i in range(3):
            mock_updates.append(MockUpdate(
                title=f'Update {i}',
                content=f'Content {i}',
                product='PostHog',
                publish_time=now - timedelta(days=i),
                tags_list=['AI Insights', 'Funnel', 'Session Replay']
            ))
        
        mock_query = MagicMock()
        mock_query.all.return_value = mock_updates
        
        with patch('services.report_generator.ProductUpdate') as MockProductUpdate:
            MockProductUpdate.tags = ComparableMock()
            MockProductUpdate.query.filter = MagicMock(return_value=mock_query)
            
            generator = ReportGenerator(llm_analyzer=mock_llm_analyzer)
            result = generator.generate_comparison_matrix()
        
        assert 'AI Insights' in result['all_tags']
        assert 'Funnel' in result['all_tags']
        assert 'Session Replay' in result['all_tags']
        assert len(result['all_tags']) == 3