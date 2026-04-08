"""
Content Classifier Service

Classifies product updates into categories: feature, bug, ai, pricing, strategy
"""

import logging
import time
from typing import Dict, List, Optional
from models import ProductUpdate, db
from services.llm_analyzer import LLMAnalyzer

logger = logging.getLogger(__name__)


class ContentClassifier:
    """
    Content Classifier
    
    Uses LLM to classify content into categories:
    - feature: New features
    - bug: Bug fixes
    - ai: AI-related updates
    - pricing: Pricing changes
    - strategy: Strategic adjustments
    """
    
    VALID_TYPES = ['feature', 'bug', 'ai', 'pricing', 'strategy']
    DEFAULT_TYPE = 'feature'
    
    def __init__(self, llm_analyzer: Optional[LLMAnalyzer] = None):
        """
        Initialize classifier
        
        Args:
            llm_analyzer: LLMAnalyzer instance (optional, will create if not provided)
        """
        self.llm_analyzer = llm_analyzer or LLMAnalyzer()
    
    def classify_update(self, update: ProductUpdate) -> str:
        """
        Classify a single product update
        
        Args:
            update: ProductUpdate object
            
        Returns:
            Classification result (feature/bug/ai/pricing/strategy)
        """
        start_time = time.time()
        
        try:
            # Skip if already classified
            if update.update_type and update.update_type in self.VALID_TYPES:
                logger.debug(f"Update {update.id} already classified as {update.update_type}")
                return update.update_type
            
            # Call LLM for classification
            classification = self.llm_analyzer.classify_content(
                title=update.title,
                content=update.content or ""
            )
            
            # Validate result
            if classification not in self.VALID_TYPES:
                logger.warning(f"Invalid classification '{classification}' for update {update.id}, using default")
                classification = self.DEFAULT_TYPE
            
            # Update the record
            update.update_type = classification
            db.session.commit()
            
            duration = (time.time() - start_time) * 1000
            logger.info(f"Classified update {update.id} as {classification} in {duration:.2f}ms")
            
            return classification
            
        except Exception as e:
            logger.error(f"Error classifying update {update.id}: {str(e)}")
            # Fallback: use default value
            update.update_type = self.DEFAULT_TYPE
            db.session.commit()
            return self.DEFAULT_TYPE
    
    def classify_batch(self, updates: List[ProductUpdate]) -> Dict[str, str]:
        """
        Classify multiple updates in batch
        
        Args:
            updates: List of ProductUpdate objects
            
        Returns:
            Dictionary mapping update IDs to classifications
        """
        results = {}
        
        for update in updates:
            try:
                classification = self.classify_update(update)
                results[str(update.id)] = classification
            except Exception as e:
                logger.error(f"Error in batch classification for update {update.id}: {str(e)}")
                results[str(update.id)] = self.DEFAULT_TYPE
        
        logger.info(f"Batch classification complete: {len(results)} updates processed")
        return results