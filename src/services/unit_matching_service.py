"""Unit matching service for work unit migration

This service provides algorithms for matching legacy unit strings
to proper unit records using exact matching, fuzzy matching, and
similarity-based approaches.
"""

import re
from typing import List, Dict, Tuple, Optional
from difflib import SequenceMatcher
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..data.models.sqlalchemy_models import Unit, Work
from ..data.database_manager import DatabaseManager


class UnitMatchingService:
    """Service for matching legacy unit strings to unit records"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._unit_cache = None
        self._abbreviation_map = self._build_abbreviation_map()
    
    def _build_abbreviation_map(self) -> Dict[str, str]:
        """Build mapping of common unit abbreviations to standard forms"""
        return {
            # Length units
            'м': 'м',
            'метр': 'м',
            'метры': 'м',
            'метров': 'м',
            'mm': 'мм',
            'мм': 'мм',
            'миллиметр': 'мм',
            'миллиметры': 'мм',
            'миллиметров': 'мм',
            'см': 'см',
            'сантиметр': 'см',
            'сантиметры': 'см',
            'сантиметров': 'см',
            'км': 'км',
            'километр': 'км',
            'километры': 'км',
            'километров': 'км',
            
            # Area units
            'м2': 'м²',
            'м²': 'м²',
            'кв.м': 'м²',
            'кв м': 'м²',
            'квм': 'м²',
            'квадратный метр': 'м²',
            'квадратные метры': 'м²',
            'квадратных метров': 'м²',
            'см2': 'см²',
            'см²': 'см²',
            'кв.см': 'см²',
            'кв см': 'см²',
            
            # Volume units
            'м3': 'м³',
            'м³': 'м³',
            'куб.м': 'м³',
            'куб м': 'м³',
            'кубический метр': 'м³',
            'кубические метры': 'м³',
            'кубических метров': 'м³',
            'л': 'л',
            'литр': 'л',
            'литры': 'л',
            'литров': 'л',
            
            # Weight units
            'кг': 'кг',
            'килограмм': 'кг',
            'килограммы': 'кг',
            'килограммов': 'кг',
            'г': 'г',
            'грамм': 'г',
            'граммы': 'г',
            'граммов': 'г',
            'т': 'т',
            'тонна': 'т',
            'тонны': 'т',
            'тонн': 'т',
            
            # Count units
            'шт': 'шт',
            'штука': 'шт',
            'штуки': 'шт',
            'штук': 'шт',
            'пара': 'пара',
            'пары': 'пара',
            'пар': 'пара',
            'комплект': 'комплект',
            'комплекты': 'комплект',
            'комплектов': 'комплект',
            'набор': 'набор',
            'наборы': 'набор',
            'наборов': 'набор',
            
            # Time units
            'час': 'час',
            'часы': 'час',
            'часов': 'час',
            'ч': 'час',
            'день': 'день',
            'дни': 'день',
            'дней': 'день',
            'смена': 'смена',
            'смены': 'смена',
            'смен': 'смена',
            
            # Special units
            'п.м': 'п.м',
            'погонный метр': 'п.м',
            'погонные метры': 'п.м',
            'погонных метров': 'п.м',
            'норма': 'норма',
            'нормы': 'норма',
            'норм': 'норма',
        }
    
    def _get_units_cache(self) -> List[Unit]:
        """Get cached list of all units"""
        if self._unit_cache is None:
            with self.db_manager.get_session() as session:
                self._unit_cache = session.query(Unit).filter(
                    Unit.marked_for_deletion == False
                ).all()
        return self._unit_cache
    
    def _normalize_unit_string(self, unit_str: str) -> str:
        """Normalize unit string for matching"""
        if not unit_str:
            return ""
        
        # Convert to lowercase and strip whitespace
        normalized = unit_str.lower().strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Handle common abbreviations before removing punctuation
        if normalized in self._abbreviation_map:
            normalized = self._abbreviation_map[normalized]
        
        # Remove common punctuation and try abbreviation mapping again
        normalized_no_punct = re.sub(r'[.,;:!?]', '', normalized)
        if normalized_no_punct in self._abbreviation_map:
            normalized = self._abbreviation_map[normalized_no_punct]
        else:
            normalized = normalized_no_punct
        
        return normalized
    
    def exact_match(self, legacy_unit: str) -> Optional[Unit]:
        """Find exact match for legacy unit string"""
        normalized_legacy = self._normalize_unit_string(legacy_unit)
        
        if not normalized_legacy:
            return None
        
        units = self._get_units_cache()
        
        # Try exact match with normalized strings
        for unit in units:
            normalized_unit = self._normalize_unit_string(unit.name)
            if normalized_unit == normalized_legacy:
                return unit
        
        return None
    
    def fuzzy_match(self, legacy_unit: str, min_similarity: float = 0.8) -> List[Tuple[Unit, float]]:
        """Find fuzzy matches for legacy unit string"""
        normalized_legacy = self._normalize_unit_string(legacy_unit)
        
        if not normalized_legacy:
            return []
        
        units = self._get_units_cache()
        matches = []
        
        for unit in units:
            normalized_unit = self._normalize_unit_string(unit.name)
            
            # Calculate similarity using SequenceMatcher
            similarity = SequenceMatcher(None, normalized_legacy, normalized_unit).ratio()
            
            if similarity >= min_similarity:
                matches.append((unit, similarity))
        
        # Sort by similarity (highest first)
        matches.sort(key=lambda x: x[1], reverse=True)
        
        return matches
    
    def similarity_match(self, legacy_unit: str, max_results: int = 5) -> List[Tuple[Unit, float]]:
        """Find similarity-based matches for legacy unit string"""
        normalized_legacy = self._normalize_unit_string(legacy_unit)
        
        if not normalized_legacy:
            return []
        
        units = self._get_units_cache()
        matches = []
        
        for unit in units:
            normalized_unit = self._normalize_unit_string(unit.name)
            
            # Calculate multiple similarity metrics
            sequence_similarity = SequenceMatcher(None, normalized_legacy, normalized_unit).ratio()
            
            # Check for substring matches
            substring_bonus = 0.0
            if normalized_legacy in normalized_unit or normalized_unit in normalized_legacy:
                substring_bonus = 0.2
            
            # Check for word matches
            legacy_words = set(normalized_legacy.split())
            unit_words = set(normalized_unit.split())
            word_overlap = len(legacy_words.intersection(unit_words))
            word_bonus = word_overlap * 0.1
            
            # Combined similarity score
            total_similarity = sequence_similarity + substring_bonus + word_bonus
            total_similarity = min(total_similarity, 1.0)  # Cap at 1.0
            
            matches.append((unit, total_similarity))
        
        # Sort by similarity (highest first) and limit results
        matches.sort(key=lambda x: x[1], reverse=True)
        
        return matches[:max_results]
    
    def find_best_match(self, legacy_unit: str) -> Tuple[Optional[Unit], float, str]:
        """Find the best match for a legacy unit string
        
        Returns:
            Tuple of (matched_unit, confidence_score, match_type)
        """
        if not legacy_unit or not legacy_unit.strip():
            return None, 0.0, 'no_input'
        
        # Try exact match first
        exact_unit = self.exact_match(legacy_unit)
        if exact_unit:
            return exact_unit, 1.0, 'exact'
        
        # Try fuzzy match with high threshold
        fuzzy_matches = self.fuzzy_match(legacy_unit, min_similarity=0.9)
        if fuzzy_matches:
            unit, similarity = fuzzy_matches[0]
            return unit, similarity, 'fuzzy_high'
        
        # Try fuzzy match with medium threshold
        fuzzy_matches = self.fuzzy_match(legacy_unit, min_similarity=0.7)
        if fuzzy_matches:
            unit, similarity = fuzzy_matches[0]
            return unit, similarity, 'fuzzy_medium'
        
        # Try similarity match
        similarity_matches = self.similarity_match(legacy_unit, max_results=1)
        if similarity_matches:
            unit, similarity = similarity_matches[0]
            if similarity >= 0.5:  # Minimum threshold for similarity match
                return unit, similarity, 'similarity'
        
        # No good match found
        return None, 0.0, 'no_match'
    
    def batch_match_units(self, legacy_units: List[str]) -> Dict[str, Tuple[Optional[Unit], float, str]]:
        """Batch match multiple legacy unit strings"""
        results = {}
        
        for legacy_unit in legacy_units:
            unit, confidence, match_type = self.find_best_match(legacy_unit)
            results[legacy_unit] = (unit, confidence, match_type)
        
        return results
    
    def get_match_statistics(self, legacy_units: List[str]) -> Dict[str, int]:
        """Get statistics for matching results"""
        results = self.batch_match_units(legacy_units)
        
        stats = {
            'total': len(legacy_units),
            'exact': 0,
            'fuzzy_high': 0,
            'fuzzy_medium': 0,
            'similarity': 0,
            'no_match': 0,
            'no_input': 0
        }
        
        for _, (unit, confidence, match_type) in results.items():
            if match_type in stats:
                stats[match_type] += 1
        
        return stats
    
    def suggest_new_units(self, unmatched_units: List[str]) -> List[str]:
        """Suggest new units to create based on unmatched legacy units"""
        suggestions = []
        
        for unit_str in unmatched_units:
            normalized = self._normalize_unit_string(unit_str)
            if normalized and normalized not in suggestions:
                suggestions.append(normalized)
        
        return suggestions
    
    def clear_cache(self):
        """Clear the units cache (call after units are added/modified)"""
        self._unit_cache = None