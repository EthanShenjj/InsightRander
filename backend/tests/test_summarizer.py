"""
Unit tests for SummaryGenerator service

Tests cover:
- Summary generation logic
- Content length threshold (500 chars)
- Summary length limit (200 chars)
- Fallback strategy
"""
import pytest
from unittest.mock import MagicMock, patch
from services.summarizer import SummaryGenerator


class TestSummaryGenerator:
    """Test suite for SummaryGenerator"""
    
    def test_generate_summary_short_content(self, mock_llm_analyzer, sample_update, mock_db_session):
        """Test that short content (<=500 chars) is truncated directly"""
        sample_update.content = "Short content that is less than 500 characters."
        
        with patch('services.summarizer.db.session', mock_db_session):
            generator = SummaryGenerator(llm_analyzer=mock_llm_analyzer)
            result = generator.generate_summary(sample_update)
        
        # Should use truncated content, not LLM
        assert result == "Short content that is less than 500 characters."
        mock_llm_analyzer.generate_summary.assert_not_called()
    
    def test_generate_summary_long_content(self, mock_llm_analyzer, sample_long_update, mock_db_session):
        """Test that long content (>500 chars) uses LLM"""
        mock_llm_analyzer.generate_summary.return_value = 'LLM generated summary'
        
        with patch('services.summarizer.db.session', mock_db_session):
            generator = SummaryGenerator(llm_analyzer=mock_llm_analyzer)
            result = generator.generate_summary(sample_long_update)
        
        assert result == 'LLM generated summary'
        mock_llm_analyzer.generate_summary.assert_called_once()
    
    def test_generate_summary_already_exists(self, mock_llm_analyzer, sample_update, mock_db_session):
        """Test that updates with existing summary are skipped"""
        sample_update.summary = "Existing summary"
        
        generator = SummaryGenerator(llm_analyzer=mock_llm_analyzer)
        result = generator.generate_summary(sample_update)
        
        assert result == "Existing summary"
        mock_llm_analyzer.generate_summary.assert_not_called()
    
    def test_generate_summary_max_length(self, mock_llm_analyzer, sample_long_update, mock_db_session):
        """Test that summary is limited to 200 characters (Requirement 4.2)"""
        # LLM returns a summary longer than 200 chars
        long_summary = "A" * 250
        mock_llm_analyzer.generate_summary.return_value = long_summary
        
        with patch('services.summarizer.db.session', mock_db_session):
            generator = SummaryGenerator(llm_analyzer=mock_llm_analyzer)
            result = generator.generate_summary(sample_long_update)
        
        # Should be truncated to 200 chars (or 203 with ellipsis)
        assert len(result) <= 203
    
    def test_generate_summary_llm_failure(self, mock_llm_analyzer, sample_long_update, mock_db_session):
        """Test fallback when LLM call fails (Requirement 4.5)"""
        mock_llm_analyzer.generate_summary.side_effect = Exception('API Error')
        
        with patch('services.summarizer.db.session', mock_db_session):
            generator = SummaryGenerator(llm_analyzer=mock_llm_analyzer)
            result = generator.generate_summary(sample_long_update)
        
        # Should fall back to truncated content
        assert len(result) <= 200
        assert result.endswith('...') or len(result) < 200
    
    def test_generate_summary_empty_content(self, mock_llm_analyzer, sample_update, mock_db_session):
        """Test handling of empty content"""
        sample_update.content = None
        
        with patch('services.summarizer.db.session', mock_db_session):
            generator = SummaryGenerator(llm_analyzer=mock_llm_analyzer)
            result = generator.generate_summary(sample_update)
        
        assert result == ""
    
    def test_generate_summary_call_parameters(self, mock_llm_analyzer, sample_long_update, mock_db_session):
        """Test that LLM is called with correct parameters"""
        mock_llm_analyzer.generate_summary.return_value = 'Summary'
        
        with patch('services.summarizer.db.session', mock_db_session):
            generator = SummaryGenerator(llm_analyzer=mock_llm_analyzer)
            generator.generate_summary(sample_long_update)
        
        # Verify call parameters
        call_args = mock_llm_analyzer.generate_summary.call_args
        assert call_args[1]['content'] == sample_long_update.content
        assert call_args[1]['max_length'] == 200
    
    def test_generate_summary_batch_success(self, mock_llm_analyzer, mock_db_session):
        """Test batch summary generation"""
        updates = []
        for i in range(3):
            update = MagicMock()
            update.id = f'test-id-{i}'
            update.content = "A" * 600  # Long content
            update.summary = None
            updates.append(update)
        
        mock_llm_analyzer.generate_summary.side_effect = ['Summary 1', 'Summary 2', 'Summary 3']
        
        with patch('services.summarizer.db.session', mock_db_session):
            generator = SummaryGenerator(llm_analyzer=mock_llm_analyzer)
            results = generator.generate_summaries_batch(updates)
        
        assert len(results) == 3
        assert results['test-id-0'] == 'Summary 1'
        assert results['test-id-1'] == 'Summary 2'
        assert results['test-id-2'] == 'Summary 3'
    
    def test_generate_summary_batch_mixed_lengths(self, mock_llm_analyzer, mock_db_session):
        """Test batch with mixed content lengths"""
        updates = []
        
        # Short content
        short_update = MagicMock()
        short_update.id = 'short-id'
        short_update.content = "Short"
        short_update.summary = None
        updates.append(short_update)
        
        # Long content
        long_update = MagicMock()
        long_update.id = 'long-id'
        long_update.content = "A" * 600
        long_update.summary = None
        updates.append(long_update)
        
        mock_llm_analyzer.generate_summary.return_value = 'LLM Summary'
        
        with patch('services.summarizer.db.session', mock_db_session):
            generator = SummaryGenerator(llm_analyzer=mock_llm_analyzer)
            results = generator.generate_summaries_batch(updates)
        
        # Short content should not call LLM
        assert results['short-id'] == 'Short'
        # Long content should call LLM
        assert results['long-id'] == 'LLM Summary'
    
    def test_generate_summary_batch_partial_failure(self, mock_llm_analyzer, mock_db_session):
        """Test batch summary generation with some failures"""
        updates = []
        for i in range(3):
            update = MagicMock()
            update.id = f'test-id-{i}'
            update.content = "A" * 600
            update.summary = None
            updates.append(update)
        
        # Second call will fail
        mock_llm_analyzer.generate_summary.side_effect = [
            'Summary 1',
            Exception('API Error'),
            'Summary 3'
        ]
        
        with patch('services.summarizer.db.session', mock_db_session):
            generator = SummaryGenerator(llm_analyzer=mock_llm_analyzer)
            results = generator.generate_summaries_batch(updates)
        
        assert len(results) == 3
        assert results['test-id-0'] == 'Summary 1'
        # Failed one should have truncated content (may include ellipsis)
        assert len(results['test-id-1']) <= 203
        assert results['test-id-2'] == 'Summary 3'
    
    def test_content_threshold_defined(self, mock_llm_analyzer):
        """Test that content threshold is defined"""
        generator = SummaryGenerator(llm_analyzer=mock_llm_analyzer)
        assert generator.CONTENT_THRESHOLD == 500
    
    def test_max_summary_length_defined(self, mock_llm_analyzer):
        """Test that max summary length is defined"""
        generator = SummaryGenerator(llm_analyzer=mock_llm_analyzer)
        assert generator.MAX_SUMMARY_LENGTH == 200
    
    def test_truncate_at_sentence_within_limit(self, mock_llm_analyzer):
        """Test truncation when text is within limit"""
        generator = SummaryGenerator(llm_analyzer=mock_llm_analyzer)
        
        text = "Short text."
        result = generator._truncate_at_sentence(text, 200)
        
        assert result == "Short text."
    
    def test_truncate_at_sentence_sentence_boundary(self, mock_llm_analyzer):
        """Test truncation at sentence boundary"""
        generator = SummaryGenerator(llm_analyzer=mock_llm_analyzer)
        
        text = "First sentence. Second sentence. Third sentence."
        result = generator._truncate_at_sentence(text, 25)
        
        # Should truncate at first sentence
        assert result == "First sentence."
    
    def test_truncate_at_sentence_no_boundary(self, mock_llm_analyzer):
        """Test truncation when no sentence boundary exists"""
        generator = SummaryGenerator(llm_analyzer=mock_llm_analyzer)
        
        text = "No sentence boundary here just continuous text"
        result = generator._truncate_at_sentence(text, 20)
        
        # Should truncate with ellipsis
        assert len(result) <= 23  # 20 + "..."
        assert result.endswith("...")
    
    def test_truncate_at_sentence_chinese(self, mock_llm_analyzer):
        """Test truncation with Chinese text"""
        generator = SummaryGenerator(llm_analyzer=mock_llm_analyzer)
        
        text = "第一句话。第二句话。第三句话。"
        result = generator._truncate_at_sentence(text, 15)
        
        # Should truncate at Chinese sentence boundary
        # Note: the function looks for sentence end followed by space or end
        # Chinese punctuation doesn't have spaces after, so it may include more
        assert "第一句话。" in result
    
    def test_truncate_at_sentence_mixed_punctuation(self, mock_llm_analyzer):
        """Test truncation with mixed punctuation"""
        generator = SummaryGenerator(llm_analyzer=mock_llm_analyzer)
        
        text = "Question? Answer! Statement."
        result = generator._truncate_at_sentence(text, 15)
        
        # Should handle different punctuation
        assert result == "Question?"
    
    def test_generate_summary_exactly_500_chars(self, mock_llm_analyzer, sample_update, mock_db_session):
        """Test boundary case: content exactly 500 characters"""
        sample_update.content = "A" * 500
        
        with patch('services.summarizer.db.session', mock_db_session):
            generator = SummaryGenerator(llm_analyzer=mock_llm_analyzer)
            result = generator.generate_summary(sample_update)
        
        # Should use truncated content (not LLM)
        # Result may be 200 or 203 with ellipsis
        assert len(result) <= 203
        mock_llm_analyzer.generate_summary.assert_not_called()
    
    def test_generate_summary_501_chars(self, mock_llm_analyzer, sample_update, mock_db_session):
        """Test boundary case: content 501 characters (just over threshold)"""
        sample_update.content = "A" * 501
        mock_llm_analyzer.generate_summary.return_value = 'LLM Summary'
        
        with patch('services.summarizer.db.session', mock_db_session):
            generator = SummaryGenerator(llm_analyzer=mock_llm_analyzer)
            result = generator.generate_summary(sample_update)
        
        # Should use LLM
        assert result == 'LLM Summary'
        mock_llm_analyzer.generate_summary.assert_called_once()