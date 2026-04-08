"""
Unit tests for TagGenerator service

Tests cover:
- Tag generation logic
- Tag count limit (max 5)
- Predefined tag validation
- Fallback strategy
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from services.tagger import TagGenerator


class TestTagGenerator:
    """Test suite for TagGenerator"""
    
    def test_generate_tags_success(self, mock_llm_analyzer, sample_update, mock_db_session):
        """Test successful tag generation"""
        mock_llm_analyzer.generate_tags.return_value = ['AI Insights', 'Product Analytics', 'Funnel']
        
        with patch('services.tagger.db.session', mock_db_session):
            generator = TagGenerator(llm_analyzer=mock_llm_analyzer)
            result = generator.generate_tags(sample_update)
        
        assert len(result) == 3
        assert 'AI Insights' in result
        assert 'Product Analytics' in result
        assert 'Funnel' in result
        mock_llm_analyzer.generate_tags.assert_called_once()
    
    def test_generate_tags_already_exists(self, mock_llm_analyzer, sample_update, mock_db_session):
        """Test that updates with existing tags are skipped"""
        sample_update.tags_list = ['AI Insights', 'Funnel']
        
        generator = TagGenerator(llm_analyzer=mock_llm_analyzer)
        result = generator.generate_tags(sample_update)
        
        assert result == ['AI Insights', 'Funnel']
        mock_llm_analyzer.generate_tags.assert_not_called()
    
    def test_generate_tags_max_limit(self, mock_llm_analyzer, sample_update, mock_db_session):
        """Test that tag count is limited to 5 (Requirement 3.5)"""
        # LLM returns 7 tags
        mock_llm_analyzer.generate_tags.return_value = [
            'AI Insights', 'Product Analytics', 'Funnel',
            'Session Replay', 'A/B Testing', 'Data Warehouse',
            'Real-time Analytics'
        ]
        
        with patch('services.tagger.db.session', mock_db_session):
            generator = TagGenerator(llm_analyzer=mock_llm_analyzer)
            result = generator.generate_tags(sample_update)
        
        # Should be limited to 5
        assert len(result) == 5
        assert result == ['AI Insights', 'Product Analytics', 'Funnel', 'Session Replay', 'A/B Testing']
    
    def test_generate_tags_invalid_tags_filtered(self, mock_llm_analyzer, sample_update, mock_db_session):
        """Test that invalid tags are filtered out"""
        mock_llm_analyzer.generate_tags.return_value = [
            'AI Insights',
            'Invalid Tag',
            'Funnel',
            'Another Invalid Tag'
        ]
        
        with patch('services.tagger.db.session', mock_db_session):
            generator = TagGenerator(llm_analyzer=mock_llm_analyzer)
            result = generator.generate_tags(sample_update)
        
        # Only valid tags should remain
        assert len(result) == 2
        assert 'AI Insights' in result
        assert 'Funnel' in result
        assert 'Invalid Tag' not in result
    
    def test_generate_tags_case_insensitive(self, mock_llm_analyzer, sample_update, mock_db_session):
        """Test that tag matching is case-insensitive"""
        mock_llm_analyzer.generate_tags.return_value = [
            'ai insights',  # lowercase
            'FUNNEL',       # uppercase
            'product analytics'  # lowercase
        ]
        
        with patch('services.tagger.db.session', mock_db_session):
            generator = TagGenerator(llm_analyzer=mock_llm_analyzer)
            result = generator.generate_tags(sample_update)
        
        # Should be normalized to proper case
        assert 'AI Insights' in result
        assert 'Funnel' in result
        assert 'Product Analytics' in result
    
    def test_generate_tags_duplicate_removal(self, mock_llm_analyzer, sample_update, mock_db_session):
        """Test that duplicate tags are removed"""
        mock_llm_analyzer.generate_tags.return_value = [
            'AI Insights',
            'AI Insights',  # duplicate
            'Funnel',
            'ai insights'   # duplicate with different case
        ]
        
        with patch('services.tagger.db.session', mock_db_session):
            generator = TagGenerator(llm_analyzer=mock_llm_analyzer)
            result = generator.generate_tags(sample_update)
        
        # Should have only 2 unique tags
        assert len(result) == 2
        assert 'AI Insights' in result
        assert 'Funnel' in result
    
    def test_generate_tags_llm_failure(self, mock_llm_analyzer, sample_update, mock_db_session):
        """Test fallback when LLM call fails (Requirement 3.6)"""
        mock_llm_analyzer.generate_tags.side_effect = Exception('API Error')
        
        with patch('services.tagger.db.session', mock_db_session):
            generator = TagGenerator(llm_analyzer=mock_llm_analyzer)
            result = generator.generate_tags(sample_update)
        
        # Should return empty list on failure
        assert result == []
    
    def test_generate_tags_empty_result(self, mock_llm_analyzer, sample_update, mock_db_session):
        """Test when LLM returns empty list"""
        mock_llm_analyzer.generate_tags.return_value = []
        
        with patch('services.tagger.db.session', mock_db_session):
            generator = TagGenerator(llm_analyzer=mock_llm_analyzer)
            result = generator.generate_tags(sample_update)
        
        assert result == []
    
    def test_generate_tags_call_parameters(self, mock_llm_analyzer, sample_update, mock_db_session):
        """Test that LLM is called with correct parameters"""
        sample_update.update_type = 'feature'
        mock_llm_analyzer.generate_tags.return_value = ['AI Insights']
        
        with patch('services.tagger.db.session', mock_db_session):
            generator = TagGenerator(llm_analyzer=mock_llm_analyzer)
            generator.generate_tags(sample_update)
        
        # Verify call parameters
        call_args = mock_llm_analyzer.generate_tags.call_args
        assert call_args[1]['title'] == sample_update.title
        assert call_args[1]['content'] == sample_update.content
        assert call_args[1]['update_type'] == 'feature'
    
    def test_generate_tags_batch_success(self, mock_llm_analyzer, mock_db_session):
        """Test batch tag generation"""
        updates = []
        for i in range(3):
            update = MagicMock()
            update.id = f'test-id-{i}'
            update.title = f'Title {i}'
            update.content = f'Content {i}'
            update.update_type = 'feature'
            update.tags_list = []
            updates.append(update)
        
        mock_llm_analyzer.generate_tags.side_effect = [
            ['AI Insights'],
            ['Funnel', 'Session Replay'],
            ['Product Analytics', 'A/B Testing', 'Data Warehouse']
        ]
        
        with patch('services.tagger.db.session', mock_db_session):
            generator = TagGenerator(llm_analyzer=mock_llm_analyzer)
            results = generator.generate_tags_batch(updates)
        
        assert len(results) == 3
        assert results['test-id-0'] == ['AI Insights']
        assert results['test-id-1'] == ['Funnel', 'Session Replay']
        assert len(results['test-id-2']) == 3
    
    def test_generate_tags_batch_partial_failure(self, mock_llm_analyzer, mock_db_session):
        """Test batch tag generation with some failures"""
        updates = []
        for i in range(3):
            update = MagicMock()
            update.id = f'test-id-{i}'
            update.title = f'Title {i}'
            update.content = f'Content {i}'
            update.update_type = 'feature'
            update.tags_list = []
            updates.append(update)
        
        # Second call will fail
        mock_llm_analyzer.generate_tags.side_effect = [
            ['AI Insights'],
            Exception('API Error'),
            ['Funnel']
        ]
        
        with patch('services.tagger.db.session', mock_db_session):
            generator = TagGenerator(llm_analyzer=mock_llm_analyzer)
            results = generator.generate_tags_batch(updates)
        
        assert len(results) == 3
        assert results['test-id-0'] == ['AI Insights']
        assert results['test-id-1'] == []  # Fallback to empty
        assert results['test-id-2'] == ['Funnel']
    
    def test_predefined_tags_defined(self, mock_llm_analyzer):
        """Test that predefined tags are defined"""
        generator = TagGenerator(llm_analyzer=mock_llm_analyzer)
        expected_tags = [
            "A/B Testing",
            "Funnel",
            "Session Replay",
            "AI Insights",
            "Data Warehouse",
            "Real-time Analytics",
            "User Segmentation",
            "Retention Analysis",
            "Cohort Analysis",
            "Product Analytics"
        ]
        assert generator.PREDEFINED_TAGS == expected_tags
        assert len(generator.PREDEFINED_TAGS) == 10
    
    def test_max_tags_limit_defined(self, mock_llm_analyzer):
        """Test that max tags limit is defined"""
        generator = TagGenerator(llm_analyzer=mock_llm_analyzer)
        assert generator.MAX_TAGS == 5
    
    def test_normalize_tag_valid(self, mock_llm_analyzer):
        """Test tag normalization for valid tags"""
        generator = TagGenerator(llm_analyzer=mock_llm_analyzer)
        
        # Test exact match
        assert generator._normalize_tag('AI Insights') == 'AI Insights'
        
        # Test case-insensitive
        assert generator._normalize_tag('ai insights') == 'AI Insights'
        assert generator._normalize_tag('FUNNEL') == 'Funnel'
    
    def test_normalize_tag_invalid(self, mock_llm_analyzer):
        """Test tag normalization for invalid tags"""
        generator = TagGenerator(llm_analyzer=mock_llm_analyzer)
        
        assert generator._normalize_tag('Invalid Tag') is None
        assert generator._normalize_tag('') is None
        assert generator._normalize_tag(None) is None
    
    def test_generate_tags_with_whitespace(self, mock_llm_analyzer, sample_update, mock_db_session):
        """Test that tags with whitespace are handled correctly"""
        mock_llm_analyzer.generate_tags.return_value = [
            '  AI Insights  ',  # leading/trailing whitespace
            '\tFunnel\t',       # tab characters
        ]
        
        with patch('services.tagger.db.session', mock_db_session):
            generator = TagGenerator(llm_analyzer=mock_llm_analyzer)
            result = generator.generate_tags(sample_update)
        
        assert 'AI Insights' in result
        assert 'Funnel' in result