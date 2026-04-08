"""
Unit tests for ContentClassifier service

Tests cover:
- Classification logic
- Fallback/degradation strategy
- Batch processing
- Performance requirements (< 200ms)
"""
import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime
from services.classifier import ContentClassifier


class TestContentClassifier:
    """Test suite for ContentClassifier"""
    
    def test_classify_update_success(self, mock_llm_analyzer, sample_update, mock_db_session):
        """Test successful classification"""
        mock_llm_analyzer.classify_content.return_value = 'ai'
        
        with patch('services.classifier.db.session', mock_db_session):
            classifier = ContentClassifier(llm_analyzer=mock_llm_analyzer)
            result = classifier.classify_update(sample_update)
        
        assert result == 'ai'
        assert sample_update.update_type == 'ai'
        mock_llm_analyzer.classify_content.assert_called_once_with(
            title=sample_update.title,
            content=sample_update.content
        )
        mock_db_session.commit.assert_called_once()
    
    def test_classify_update_already_classified(self, mock_llm_analyzer, sample_update, mock_db_session):
        """Test that already classified updates are skipped"""
        sample_update.update_type = 'bug'
        
        classifier = ContentClassifier(llm_analyzer=mock_llm_analyzer)
        result = classifier.classify_update(sample_update)
        
        assert result == 'bug'
        mock_llm_analyzer.classify_content.assert_not_called()
        mock_db_session.commit.assert_not_called()
    
    def test_classify_update_invalid_result(self, mock_llm_analyzer, sample_update, mock_db_session):
        """Test fallback when LLM returns invalid classification"""
        mock_llm_analyzer.classify_content.return_value = 'invalid_type'
        
        with patch('services.classifier.db.session', mock_db_session):
            classifier = ContentClassifier(llm_analyzer=mock_llm_analyzer)
            result = classifier.classify_update(sample_update)
        
        # Should fall back to default 'feature'
        assert result == 'feature'
        assert sample_update.update_type == 'feature'
    
    def test_classify_update_llm_failure(self, mock_llm_analyzer, sample_update, mock_db_session):
        """Test fallback when LLM call fails"""
        mock_llm_analyzer.classify_content.side_effect = Exception('API Error')
        
        with patch('services.classifier.db.session', mock_db_session):
            classifier = ContentClassifier(llm_analyzer=mock_llm_analyzer)
            result = classifier.classify_update(sample_update)
        
        # Should fall back to default 'feature'
        assert result == 'feature'
        assert sample_update.update_type == 'feature'
        mock_db_session.commit.assert_called()
    
    def test_classify_update_empty_content(self, mock_llm_analyzer, sample_update, mock_db_session):
        """Test classification with empty content"""
        sample_update.content = None
        mock_llm_analyzer.classify_content.return_value = 'strategy'
        
        with patch('services.classifier.db.session', mock_db_session):
            classifier = ContentClassifier(llm_analyzer=mock_llm_analyzer)
            result = classifier.classify_update(sample_update)
        
        assert result == 'strategy'
        mock_llm_analyzer.classify_content.assert_called_once_with(
            title=sample_update.title,
            content=""
        )
    
    def test_classify_all_valid_types(self, mock_llm_analyzer, sample_update, mock_db_session):
        """Test that all valid classification types are accepted"""
        valid_types = ['feature', 'bug', 'ai', 'pricing', 'strategy']
        
        for classification_type in valid_types:
            mock_llm_analyzer.reset_mock()
            mock_db_session.reset_mock()
            sample_update.update_type = None
            
            mock_llm_analyzer.classify_content.return_value = classification_type
            
            with patch('services.classifier.db.session', mock_db_session):
                classifier = ContentClassifier(llm_analyzer=mock_llm_analyzer)
                result = classifier.classify_update(sample_update)
            
            assert result == classification_type
            assert sample_update.update_type == classification_type
    
    def test_classify_batch_success(self, mock_llm_analyzer, mock_db_session):
        """Test batch classification"""
        updates = []
        for i in range(3):
            update = MagicMock()
            update.id = f'test-id-{i}'
            update.title = f'Title {i}'
            update.content = f'Content {i}'
            update.update_type = None
            updates.append(update)
        
        mock_llm_analyzer.classify_content.side_effect = ['feature', 'bug', 'ai']
        
        with patch('services.classifier.db.session', mock_db_session):
            classifier = ContentClassifier(llm_analyzer=mock_llm_analyzer)
            results = classifier.classify_batch(updates)
        
        assert len(results) == 3
        assert results['test-id-0'] == 'feature'
        assert results['test-id-1'] == 'bug'
        assert results['test-id-2'] == 'ai'
    
    def test_classify_batch_partial_failure(self, mock_llm_analyzer, mock_db_session):
        """Test batch classification with some failures"""
        updates = []
        for i in range(3):
            update = MagicMock()
            update.id = f'test-id-{i}'
            update.title = f'Title {i}'
            update.content = f'Content {i}'
            update.update_type = None
            updates.append(update)
        
        # Second call will fail
        mock_llm_analyzer.classify_content.side_effect = [
            'feature',
            Exception('API Error'),
            'ai'
        ]
        
        with patch('services.classifier.db.session', mock_db_session):
            classifier = ContentClassifier(llm_analyzer=mock_llm_analyzer)
            results = classifier.classify_batch(updates)
        
        assert len(results) == 3
        assert results['test-id-0'] == 'feature'
        assert results['test-id-1'] == 'feature'  # Fallback to default
        assert results['test-id-2'] == 'ai'
    
    def test_classify_update_performance(self, mock_llm_analyzer, sample_update, mock_db_session):
        """Test that classification completes within 200ms (Requirement 2.6)"""
        import time
        
        mock_llm_analyzer.classify_content.return_value = 'feature'
        
        with patch('services.classifier.db.session', mock_db_session):
            classifier = ContentClassifier(llm_analyzer=mock_llm_analyzer)
            
            start_time = time.time()
            classifier.classify_update(sample_update)
            duration_ms = (time.time() - start_time) * 1000
        
        # Should complete within 200ms
        assert duration_ms < 200, f"Classification took {duration_ms:.2f}ms, expected < 200ms"
    
    def test_classify_update_call_parameters(self, mock_llm_analyzer, sample_update, mock_db_session):
        """Test that LLM is called with correct parameters"""
        mock_llm_analyzer.classify_content.return_value = 'feature'
        
        with patch('services.classifier.db.session', mock_db_session):
            classifier = ContentClassifier(llm_analyzer=mock_llm_analyzer)
            classifier.classify_update(sample_update)
        
        # Verify call parameters
        call_args = mock_llm_analyzer.classify_content.call_args
        assert call_args[1]['title'] == sample_update.title
        assert call_args[1]['content'] == sample_update.content
    
    def test_default_type_is_feature(self, mock_llm_analyzer):
        """Test that default classification type is 'feature'"""
        classifier = ContentClassifier(llm_analyzer=mock_llm_analyzer)
        assert classifier.DEFAULT_TYPE == 'feature'
    
    def test_valid_types_defined(self, mock_llm_analyzer):
        """Test that all valid types are defined"""
        classifier = ContentClassifier(llm_analyzer=mock_llm_analyzer)
        expected_types = ['feature', 'bug', 'ai', 'pricing', 'strategy']
        assert classifier.VALID_TYPES == expected_types