"""
Metrics-based transaction analysis using existing prediction data
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import re
from app.model_metrics import get_predictions_data

logger = logging.getLogger(__name__)

class MetricsTransactionAnalyzer:
    def __init__(self):
        self.predictions_cache = None
        self.cache_timestamp = None
        self.cache_ttl = 300  # 5 minutes cache
    
    def _get_predictions(self) -> List[Dict]:
        """Get predictions with caching"""
        now = datetime.now()
        
        if (self.predictions_cache is None or 
            self.cache_timestamp is None or 
            (now - self.cache_timestamp).seconds > self.cache_ttl):
            
            logger.info("🔄 Loading fresh predictions data from metrics")
            self.predictions_cache = get_predictions_data()
            self.cache_timestamp = now
            logger.info(f"✅ Loaded {len(self.predictions_cache)} predictions from metrics")
        
        return self.predictions_cache or []
    
    def analyze_transaction_patterns(self, description: str, amount: float, account: str = None) -> Dict:
        """
        Analyze transaction patterns using existing metrics data
        """
        predictions = self._get_predictions()
        
        if not predictions:
            logger.warning("No predictions data available for analysis")
            return self._empty_analysis()
        
        logger.info(f"🔍 Analyzing '{description}' against {len(predictions)} historical predictions")
        
        analysis = {
            'similar_transactions': self._find_similar_transactions(predictions, description, amount),
            'category_patterns': self._analyze_category_patterns(predictions, description),
            'spending_patterns': self._analyze_spending_patterns(predictions, amount),
            'merchant_history': self._analyze_merchant_history(predictions, description),
            'temporal_patterns': self._analyze_temporal_patterns(predictions, description),
            'confidence_patterns': self._analyze_confidence_patterns(predictions, description)
        }
        
        return analysis
    
    def _find_similar_transactions(self, predictions: List[Dict], description: str, amount: float) -> List[Dict]:
        """Find similar transactions from metrics data"""
        similar = []
        desc_lower = description.lower()
        
        for pred in predictions:
            pred_desc = pred.get('description', '').lower()
            
            # Calculate similarity
            similarity_score = self._calculate_similarity(desc_lower, pred_desc)
            
            if similarity_score > 0.3:  # Similar description
                similar.append({
                    'description': pred.get('description', ''),
                    'predicted_category': pred.get('predicted_category', ''),
                    'confidence': pred.get('confidence', 0),
                    'timestamp': pred.get('timestamp', ''),
                    'similarity_score': similarity_score
                })
        
        # Sort by similarity score
        similar.sort(key=lambda x: x['similarity_score'], reverse=True)
        return similar[:10]  # Return top 10 similar
    
    def _analyze_category_patterns(self, predictions: List[Dict], description: str) -> Dict:
        """Analyze category patterns for similar descriptions"""
        similar_transactions = self._find_similar_transactions(predictions, description, 0)
        
        if not similar_transactions:
            return {
                'suggested_category': 'Uncategorized',
                'confidence': 0.1,
                'all_categories': [],
                'reasoning': "No similar transactions found in historical data"
            }
        
        # Count categories
        category_counts = Counter()
        total_confidence = 0
        
        for transaction in similar_transactions:
            category = transaction['predicted_category']
            confidence = transaction['confidence']
            similarity = transaction['similarity_score']
            
            # Weight by similarity and confidence
            weight = similarity * confidence
            category_counts[category] += weight
            total_confidence += weight
        
        if not category_counts:
            return {
                'suggested_category': 'Uncategorized',
                'confidence': 0.1,
                'all_categories': [],
                'reasoning': "No categorized similar transactions found"
            }
        
        # Get most common category
        most_common_category = category_counts.most_common(1)[0][0]
        confidence = category_counts[most_common_category] / total_confidence if total_confidence > 0 else 0
        
        all_categories = [
            {
                'category': cat,
                'weight': weight,
                'frequency': sum(1 for t in similar_transactions if t['predicted_category'] == cat)
            }
            for cat, weight in category_counts.most_common(5)
        ]
        
        return {
            'suggested_category': most_common_category,
            'confidence': round(confidence, 3),
            'all_categories': all_categories,
            'reasoning': f"Based on {len(similar_transactions)} similar historical transactions"
        }
    
    def _analyze_spending_patterns(self, predictions: List[Dict], amount: float) -> Dict:
        """Analyze spending patterns (simplified without amounts in metrics)"""
        recent_count = len([p for p in predictions if self._is_recent(p.get('timestamp', ''))])
        total_count = len(predictions)
        
        # Simple frequency-based analysis
        if recent_count > 50:
            transaction_frequency = "High (very active spending)"
            amount_level = "normal"  # Can't determine without amounts
        elif recent_count > 20:
            transaction_frequency = "Moderate (regular spending)"
            amount_level = "normal"
        else:
            transaction_frequency = "Low (infrequent spending)"
            amount_level = "normal"
        
        return {
            'amount_level': amount_level,
            'vs_average': 'Analysis requires amount data',
            'budget_impact': 'moderate',
            'recent_spending': f"{recent_count} recent transactions",
            'transaction_frequency': transaction_frequency,
            'total_transactions': total_count
        }
    
    def _analyze_merchant_history(self, predictions: List[Dict], description: str) -> Dict:
        """Analyze merchant/vendor history from metrics"""
        merchant_terms = self._extract_merchant_terms(description)
        if not merchant_terms:
            return {'history': 'New merchant', 'frequency': 0, 'last_transaction': None}
        
        merchant_transactions = []
        for pred in predictions:
            pred_desc = pred.get('description', '').lower()
            if any(term in pred_desc for term in merchant_terms):
                merchant_transactions.append(pred)
        
        if merchant_transactions:
            # Sort by timestamp (most recent first)
            merchant_transactions.sort(
                key=lambda x: x.get('timestamp', ''), 
                reverse=True
            )
            
            most_common_category = Counter(
                t.get('predicted_category', '') for t in merchant_transactions
            ).most_common(1)
            
            return {
                'history': f"Found {len(merchant_transactions)} previous transactions",
                'frequency': len(merchant_transactions),
                'last_transaction': merchant_transactions[0].get('timestamp', ''),
                'typical_category': most_common_category[0][0] if most_common_category else 'Unknown',
                'avg_confidence': sum(t.get('confidence', 0) for t in merchant_transactions) / len(merchant_transactions)
            }
        else:
            return {'history': 'New merchant', 'frequency': 0, 'last_transaction': None}
    
    def _analyze_temporal_patterns(self, predictions: List[Dict], description: str) -> Dict:
        """Analyze temporal patterns from metrics timestamps"""
        similar_transactions = self._find_similar_transactions(predictions, description, 0)
        
        if not similar_transactions:
            return {
                'most_common_time': 'No pattern',
                'most_common_day': 'No pattern',
                'pattern_strength': '0 occurrences'
            }
        
        # Extract hour and day patterns from timestamps
        hour_counts = defaultdict(int)
        day_counts = defaultdict(int)
        
        for transaction in similar_transactions:
            timestamp_str = transaction.get('timestamp', '')
            if timestamp_str:
                try:
                    dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    hour_counts[dt.hour] += 1
                    day_counts[dt.weekday()] += 1
                except:
                    continue
        
        if hour_counts and day_counts:
            most_common_hour = max(hour_counts, key=hour_counts.get)
            most_common_day = max(day_counts, key=day_counts.get)
            
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            day_name = day_names[most_common_day] if 0 <= most_common_day < 7 else 'Unknown'
            
            return {
                'most_common_time': f"{most_common_hour:02d}:00",
                'most_common_day': day_name,
                'pattern_strength': f"{len(similar_transactions)} similar transactions analyzed"
            }
        
        return {
            'most_common_time': 'No pattern',
            'most_common_day': 'No pattern',
            'pattern_strength': 'Insufficient data'
        }
    
    def _analyze_confidence_patterns(self, predictions: List[Dict], description: str) -> Dict:
        """Analyze confidence patterns for similar transactions"""
        similar_transactions = self._find_similar_transactions(predictions, description, 0)
        
        if not similar_transactions:
            return {
                'avg_confidence': 0.5,
                'confidence_trend': 'unknown',
                'high_confidence_count': 0
            }
        
        confidences = [t.get('confidence', 0) for t in similar_transactions]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        high_confidence_count = sum(1 for c in confidences if c > 0.8)
        
        if avg_confidence > 0.8:
            confidence_trend = 'consistently high'
        elif avg_confidence > 0.6:
            confidence_trend = 'moderate'
        else:
            confidence_trend = 'variable'
        
        return {
            'avg_confidence': round(avg_confidence, 3),
            'confidence_trend': confidence_trend,
            'high_confidence_count': high_confidence_count,
            'total_similar': len(similar_transactions)
        }
    
    def _calculate_similarity(self, desc1: str, desc2: str) -> float:
        """Calculate text similarity between descriptions"""
        # Simple word-based similarity
        words1 = set(desc1.lower().split())
        words2 = set(desc2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _extract_merchant_terms(self, description: str) -> List[str]:
        """Extract likely merchant/vendor names from description"""
        # Common words to ignore
        stop_words = {'at', 'in', 'on', 'the', 'and', 'or', 'for', 'with', 'from', 'to', 'by', 'purchase', 'payment', 'transaction'}
        
        # Clean and split description
        cleaned = re.sub(r'[^\w\s]', ' ', description.lower())
        words = [w.strip() for w in cleaned.split() if w.strip() and w not in stop_words and len(w) > 2]
        
        return words[:3] if words else []
    
    def _is_recent(self, timestamp_str: str, days: int = 30) -> bool:
        """Check if timestamp is within recent days"""
        if not timestamp_str:
            return False
        
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return (datetime.now() - dt.replace(tzinfo=None)).days <= days
        except:
            return False
    
    def _empty_analysis(self) -> Dict:
        """Return empty analysis structure"""
        return {
            'similar_transactions': [],
            'category_patterns': {
                'suggested_category': 'Uncategorized',
                'confidence': 0.1,
                'all_categories': [],
                'reasoning': 'No historical data available'
            },
            'spending_patterns': {
                'amount_level': 'unknown',
                'transaction_frequency': 'No data',
                'budget_impact': 'unknown'
            },
            'merchant_history': {
                'history': 'No data',
                'frequency': 0,
                'last_transaction': None
            },
            'temporal_patterns': {
                'most_common_time': 'No pattern',
                'most_common_day': 'No pattern'
            },
            'confidence_patterns': {
                'avg_confidence': 0.5,
                'confidence_trend': 'unknown'
            }
        }

# Global instance
metrics_analyzer = MetricsTransactionAnalyzer()