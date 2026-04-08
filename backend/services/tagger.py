"""
Tag Generator Service

Generates intelligent tags for product updates
"""

import logging
from typing import Dict, List, Optional
from models import ProductUpdate, db
from services.llm_analyzer import LLMAnalyzer

logger = logging.getLogger(__name__)


class TagGenerator:
    """
    Tag Generator
    
    Generates predefined tags for product updates:
    - A/B Testing
    - Funnel
    - Session Replay
    - AI Insights
    - Data Warehouse
    - Real-time Analytics
    - User Segmentation
    - Retention Analysis
    - Cohort Analysis
    - Product Analytics
    """
    
    PREDEFINED_TAGS = [
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
    
    MAX_TAGS = 5
    
    def __init__(self, llm_analyzer: Optional[LLMAnalyzer] = None):
        """
        Initialize tag generator
        
        Args:
            llm_analyzer: LLMAnalyzer instance (optional, will create if not provided)
        """
        self.llm_analyzer = llm_analyzer or LLMAnalyzer()
    
    def generate_tags(self, update: ProductUpdate) -> List[str]:
        """
        Generate tags for a single product update
        
        Args:
            update: ProductUpdate object
            
        Returns:
            List of tags (max 5)
        """
        try:
            # Skip if already has tags
            existing_tags = update.tags_list
            if existing_tags:
                logger.debug(f"Update {update.id} already has tags: {existing_tags}")
                return existing_tags
            
            # Call LLM for tag generation
            tags = self.llm_analyzer.generate_tags(
                title=update.title,
                content=update.content or "",
                update_type=update.update_type or ""
            )
            
            # Validate and filter tags
            valid_tags = []
            for tag in tags:
                # Normalize tag to match predefined format
                normalized = self._normalize_tag(tag)
                if normalized and normalized not in valid_tags:
                    valid_tags.append(normalized)
            
            # Limit to MAX_TAGS
            valid_tags = valid_tags[:self.MAX_TAGS]
            
            # Update the record
            update.tags_list = valid_tags
            db.session.commit()
            
            logger.info(f"Generated tags for update {update.id}: {valid_tags}")
            return valid_tags
            
        except Exception as e:
            logger.error(f"Error generating tags for update {update.id}: {str(e)}")
            # Fallback: set empty tags
            update.tags_list = []
            db.session.commit()
            return []
    
    def generate_tags_batch(self, updates: List[ProductUpdate]) -> Dict[str, List[str]]:
        """
        Generate tags for multiple updates in batch
        
        Args:
            updates: List of ProductUpdate objects
            
        Returns:
            Dictionary mapping update IDs to tag lists
        """
        results = {}
        
        for update in updates:
            try:
                tags = self.generate_tags(update)
                results[str(update.id)] = tags
            except Exception as e:
                logger.error(f"Error in batch tag generation for update {update.id}: {str(e)}")
                results[str(update.id)] = []
        
        logger.info(f"Batch tag generation complete: {len(results)} updates processed")
        return results
    
    def _normalize_tag(self, tag: str) -> Optional[str]:
        """
        Normalize a tag to match predefined format
        
        Args:
            tag: Raw tag string
            
        Returns:
            Normalized tag or None if not valid
        """
        if not tag:
            return None
        
        # Strip whitespace
        tag = tag.strip()
        
        # Case-insensitive matching against predefined tags
        tag_lower = tag.lower()
        for predefined in self.PREDEFINED_TAGS:
            if predefined.lower() == tag_lower:
                return predefined
        
        # If no match found, return None (tag not in predefined list)
        logger.debug(f"Tag '{tag}' not in predefined list, ignoring")
        return None