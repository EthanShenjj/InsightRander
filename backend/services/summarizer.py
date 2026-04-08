"""
Summary Generator Service

Generates concise summaries for product updates
"""

import logging
from typing import Dict, List, Optional
from models import ProductUpdate, db
from services.llm_analyzer import LLMAnalyzer

logger = logging.getLogger(__name__)


class SummaryGenerator:
    """
    Summary Generator
    
    Generates summaries for long content (>500 chars):
    - Uses LLM for intelligent summarization
    - Falls back to truncation for short content or LLM failures
    - Max summary length: 200 characters
    """
    
    CONTENT_THRESHOLD = 500  # Only summarize content longer than this
    MAX_SUMMARY_LENGTH = 200
    
    def __init__(self, llm_analyzer: Optional[LLMAnalyzer] = None):
        """
        Initialize summary generator
        
        Args:
            llm_analyzer: LLMAnalyzer instance (optional, will create if not provided)
        """
        self.llm_analyzer = llm_analyzer or LLMAnalyzer()
    
    def generate_summary(self, update: ProductUpdate) -> str:
        """
        Generate summary for a single product update
        
        Args:
            update: ProductUpdate object
            
        Returns:
            Summary text (max 200 characters)
        """
        try:
            # Skip if already has summary
            if update.summary:
                logger.debug(f"Update {update.id} already has summary")
                return update.summary
            
            content = update.content or ""
            
            # For short content, use first 200 chars directly
            if len(content) <= self.CONTENT_THRESHOLD:
                summary = self._truncate_at_sentence(content, self.MAX_SUMMARY_LENGTH)
                update.summary = summary
                db.session.commit()
                logger.debug(f"Short content for update {update.id}, using truncated content")
                return summary
            
            # For long content, use LLM
            summary = self.llm_analyzer.generate_summary(
                content=content,
                max_length=self.MAX_SUMMARY_LENGTH
            )
            
            # Ensure summary doesn't exceed max length
            if len(summary) > self.MAX_SUMMARY_LENGTH:
                summary = self._truncate_at_sentence(summary, self.MAX_SUMMARY_LENGTH)
            
            # Update the record
            update.summary = summary
            db.session.commit()
            
            logger.info(f"Generated summary for update {update.id}: {len(summary)} chars")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary for update {update.id}: {str(e)}")
            # Fallback: use truncated content
            content = update.content or ""
            summary = self._truncate_at_sentence(content, self.MAX_SUMMARY_LENGTH)
            update.summary = summary
            db.session.commit()
            return summary
    
    def generate_summaries_batch(self, updates: List[ProductUpdate]) -> Dict[str, str]:
        """
        Generate summaries for multiple updates in batch
        
        Args:
            updates: List of ProductUpdate objects
            
        Returns:
            Dictionary mapping update IDs to summaries
        """
        results = {}
        
        for update in updates:
            try:
                summary = self.generate_summary(update)
                results[str(update.id)] = summary
            except Exception as e:
                logger.error(f"Error in batch summary generation for update {update.id}: {str(e)}")
                # Fallback: use truncated content
                content = update.content or ""
                results[str(update.id)] = self._truncate_at_sentence(content, self.MAX_SUMMARY_LENGTH)
        
        logger.info(f"Batch summary generation complete: {len(results)} updates processed")
        return results
    
    def _truncate_at_sentence(self, text: str, max_length: int) -> str:
        """
        Truncate text at sentence boundary
        
        Args:
            text: Text to truncate
            max_length: Maximum length
            
        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text
        
        # Find last sentence boundary within max_length
        truncated = text[:max_length]
        
        # Try to find sentence end (。！？.!? followed by space or end)
        for i in range(len(truncated) - 1, -1, -1):
            char = truncated[i]
            if char in '。！？.!?' and (i == len(truncated) - 1 or truncated[i + 1] == ' '):
                return truncated[:i + 1]
        
        # No sentence boundary found, just truncate with ellipsis
        return truncated.rstrip() + "..."