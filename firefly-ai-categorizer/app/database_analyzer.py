"""
Database-driven transaction analysis using real Firefly III data
"""
import aiomysql
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import os
from collections import defaultdict

logger = logging.getLogger(__name__)

class DatabaseTransactionAnalyzer:
    def __init__(self):
        self.db_config = {
            'host': os.environ.get('DB_HOST', 'db'),  # Docker service name for Firefly III DB
            'port': int(os.environ.get('DB_PORT', 3306)),  # MariaDB default port
            'db': os.environ.get('DB_DATABASE', 'firefly'),
            'user': os.environ.get('DB_USERNAME', 'admin'),  # From .db.env
            'password': os.environ.get('DB_PASSWORD', 'admin'),  # From .db.env
            'charset': 'utf8mb4'
        }
    
    async def get_connection(self):
        """Get database connection"""
        try:
            return await aiomysql.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    async def analyze_transaction_patterns(self, description: str, amount: float, account: str = None) -> Dict:
        """
        Analyze transaction patterns from real database data
        """
        conn = await self.get_connection()
        try:
            analysis = {
                'similar_transactions': await self._find_similar_transactions(conn, description, amount),
                'category_patterns': await self._analyze_category_patterns(conn, description),
                'spending_patterns': await self._analyze_spending_patterns(conn, amount, account),
                'merchant_history': await self._analyze_merchant_history(conn, description),
                'budget_impact': await self._analyze_budget_impact(conn, amount),
                'temporal_patterns': await self._analyze_temporal_patterns(conn, description)
            }
            return analysis
        finally:
            conn.close()

    async def _find_similar_transactions(self, conn, description: str, amount: float) -> List[Dict]:
        """Find similar transactions based on description and amount"""
        query = """
        SELECT 
            t.description,
            t.amount,
            c.name as category,
            t.date,
            COUNT(*) OVER (PARTITION BY c.name) as category_frequency
        FROM transactions t
        LEFT JOIN transaction_journals tj ON t.transaction_journal_id = tj.id
        LEFT JOIN categories c ON tj.category_id = c.id
        WHERE 
            (t.description LIKE %s 
             OR t.description LIKE %s
             OR %s LIKE CONCAT('%', t.description, '%'))
            AND ABS(t.amount - %s) < %s * 0.5
        ORDER BY ABS(t.amount - %s)
        LIMIT 10
        """
        
        # Extract key merchant terms from description
        merchant_terms = self._extract_merchant_terms(description)
        search_term = merchant_terms[0] if merchant_terms else description
        
        try:
            cursor = await conn.cursor()
            await cursor.execute(query, (
                f'%{description}%', 
                f'%{search_term}%', 
                description,
                abs(amount), 
                abs(amount), 
                abs(amount)
            ))
            rows = await cursor.fetchall()
            
            # Convert to dict list
            columns = ['description', 'amount', 'category', 'date', 'category_frequency']
            result = []
            for row in rows:
                result.append(dict(zip(columns, row)))
            
            await cursor.close()
            return result
        except Exception as e:
            logger.warning(f"Similar transactions query failed: {e}")
            return []

    async def _analyze_category_patterns(self, conn, description: str) -> Dict:
        """Analyze category patterns for similar descriptions"""
        query = """
        SELECT 
            c.name as category,
            COUNT(*) as frequency,
            AVG(t.amount) as avg_amount
        FROM transactions t
        LEFT JOIN transaction_journals tj ON t.transaction_journal_id = tj.id
        LEFT JOIN categories c ON tj.category_id = c.id
        WHERE c.name IS NOT NULL
            AND (t.description LIKE %s OR t.description LIKE %s)
        GROUP BY c.name
        ORDER BY frequency DESC
        LIMIT 5
        """
        
        merchant_terms = self._extract_merchant_terms(description)
        search_term = merchant_terms[0] if merchant_terms else description
        
        try:
            cursor = await conn.cursor()
            await cursor.execute(query, (f'%{description}%', f'%{search_term}%'))
            rows = await cursor.fetchall()
            
            categories = []
            for row in rows:
                categories.append({
                    'category': row[0],
                    'frequency': row[1],
                    'avg_amount': float(row[2]) if row[2] else 0,
                    'similarity_score': 0.8  # Simplified for MariaDB
                })
            
            await cursor.close()
            
            if categories:
                total_freq = sum(cat['frequency'] for cat in categories)
                most_likely = categories[0]
                confidence = most_likely['frequency'] / total_freq if total_freq > 0 else 0
                
                return {
                    'suggested_category': most_likely['category'],
                    'confidence': round(confidence, 3),
                    'all_categories': categories,
                    'reasoning': f"Based on {total_freq} similar transactions"
                }
            else:
                return {
                    'suggested_category': 'Uncategorized',
                    'confidence': 0.1,
                    'all_categories': [],
                    'reasoning': "No similar transactions found in database"
                }
        except Exception as e:
            logger.warning(f"Category patterns query failed: {e}")
            return {'suggested_category': 'Uncategorized', 'confidence': 0.1, 'all_categories': [], 'reasoning': "Database query failed"}

    async def _analyze_spending_patterns(self, conn, amount: float, account: str = None) -> Dict:
        """Analyze spending patterns and budget impact"""
        # Get recent spending for comparison
        recent_query = """
        SELECT 
            AVG(ABS(t.amount)) as avg_amount,
            STDDEV(ABS(t.amount)) as stddev_amount,
            COUNT(*) as transaction_count,
            SUM(CASE WHEN t.amount < 0 THEN ABS(t.amount) ELSE 0 END) as total_spent
        FROM transactions t
        WHERE t.date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            AND t.amount < 0
        """
        
        try:
            cursor = await conn.cursor()
            await cursor.execute(recent_query)
            row = await cursor.fetchone()
            await cursor.close()
            
            if row:
                avg_amount = float(row[0] or 0)
                stddev_amount = float(row[1] or 1)
                total_spent = float(row[3] or 0)
                transaction_count = row[2] or 0
                
                # Classify transaction amount
                amount_abs = abs(amount)
                if amount_abs > avg_amount + stddev_amount:
                    amount_level = "high"
                elif amount_abs < avg_amount - stddev_amount:
                    amount_level = "low"
                else:
                    amount_level = "normal"
                
                # Estimate budget impact
                daily_avg = total_spent / 30 if total_spent > 0 else 0
                budget_impact = "significant" if amount_abs > daily_avg * 3 else "moderate" if amount_abs > daily_avg else "minimal"
                
                return {
                    'amount_level': amount_level,
                    'vs_average': f"{((amount_abs / avg_amount - 1) * 100):+.1f}%" if avg_amount > 0 else "N/A",
                    'budget_impact': budget_impact,
                    'recent_spending': f"${total_spent:.2f}",
                    'transaction_frequency': f"{transaction_count} transactions in last 30 days"
                }
            else:
                return {
                    'amount_level': 'unknown',
                    'vs_average': 'N/A',
                    'budget_impact': 'unknown',
                    'recent_spending': 'No data',
                    'transaction_frequency': 'No recent transactions'
                }
        except Exception as e:
            logger.warning(f"Spending patterns query failed: {e}")
            return {'amount_level': 'unknown', 'vs_average': 'N/A', 'budget_impact': 'unknown'}

    async def _analyze_merchant_history(self, conn, description: str) -> Dict:
        """Analyze merchant/vendor history"""
        merchant_terms = self._extract_merchant_terms(description)
        if not merchant_terms:
            return {'history': 'New merchant', 'frequency': 0, 'last_transaction': None}
        
        # Search for transactions with this merchant
        query = """
        SELECT 
            t.description,
            t.amount,
            t.date,
            c.name as category
        FROM transactions t
        LEFT JOIN transaction_journals tj ON t.transaction_journal_id = tj.id
        LEFT JOIN categories c ON tj.category_id = c.id
        WHERE t.description LIKE %s
        ORDER BY t.date DESC
        LIMIT 10
        """
        
        try:
            cursor = await conn.cursor()
            await cursor.execute(query, (f'%{merchant_terms[0]}%',))
            rows = await cursor.fetchall()
            await cursor.close()
            
            if rows:
                transactions = []
                for row in rows:
                    transactions.append({
                        'description': row[0],
                        'amount': row[1],
                        'date': row[2],
                        'category': row[3]
                    })
                
                return {
                    'history': f"Found {len(transactions)} previous transactions",
                    'frequency': len(transactions),
                    'last_transaction': transactions[0]['date'].strftime('%Y-%m-%d') if transactions[0]['date'] else 'Unknown',
                    'typical_category': transactions[0]['category'],
                    'avg_amount': sum(abs(float(t['amount'])) for t in transactions) / len(transactions)
                }
            else:
                return {'history': 'New merchant', 'frequency': 0, 'last_transaction': None}
        except Exception as e:
            logger.warning(f"Merchant history query failed: {e}")
            return {'history': 'Query failed', 'frequency': 0, 'last_transaction': None}

    async def _analyze_budget_impact(self, conn, amount: float) -> Dict:
        """Analyze budget impact based on current month spending"""
        query = """
        SELECT 
            SUM(CASE WHEN t.amount < 0 THEN ABS(t.amount) ELSE 0 END) as month_spent,
            COUNT(CASE WHEN t.amount < 0 THEN 1 END) as month_transactions
        FROM transactions t
        WHERE YEAR(t.date) = YEAR(CURDATE()) AND MONTH(t.date) = MONTH(CURDATE())
        """
        
        try:
            cursor = await conn.cursor()
            await cursor.execute(query)
            row = await cursor.fetchone()
            await cursor.close()
            
            month_spent = float(row[0] or 0)
            month_transactions = row[1] or 0
            
            # Simple budget impact calculation
            estimated_monthly_budget = month_spent * 1.2  # Assume 20% buffer
            impact_percentage = (abs(amount) / estimated_monthly_budget * 100) if estimated_monthly_budget > 0 else 0
            
            if impact_percentage > 10:
                impact_level = "high"
            elif impact_percentage > 5:
                impact_level = "moderate"
            else:
                impact_level = "low"
            
            return {
                'impact_level': impact_level,
                'impact_percentage': f"{impact_percentage:.1f}%",
                'month_spent': f"${month_spent:.2f}",
                'month_transactions': month_transactions
            }
        except Exception as e:
            logger.warning(f"Budget impact query failed: {e}")
            return {'impact_level': 'unknown', 'impact_percentage': 'N/A'}

    async def _analyze_temporal_patterns(self, conn, description: str) -> Dict:
        """Analyze temporal spending patterns"""
        merchant_terms = self._extract_merchant_terms(description)
        search_term = merchant_terms[0] if merchant_terms else description
        
        query = """
        SELECT 
            HOUR(t.date) as hour,
            DAYOFWEEK(t.date) as day_of_week,
            COUNT(*) as frequency
        FROM transactions t
        WHERE (t.description LIKE %s OR t.description LIKE %s)
        GROUP BY HOUR(t.date), DAYOFWEEK(t.date)
        ORDER BY frequency DESC
        LIMIT 5
        """
        
        try:
            cursor = await conn.cursor()
            await cursor.execute(query, (f'%{search_term}%', f'%{description}%'))
            rows = await cursor.fetchall()
            await cursor.close()
            
            if rows:
                patterns = []
                for row in rows:
                    patterns.append({
                        'hour': row[0],
                        'day_of_week': row[1],
                        'frequency': row[2]
                    })
                
                most_common = patterns[0]
                hour = int(most_common['hour']) if most_common['hour'] else 12
                dow = int(most_common['day_of_week']) if most_common['day_of_week'] else 1
                
                day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
                day_name = day_names[dow - 1] if 1 <= dow <= 7 else 'Unknown'  # MySQL DAYOFWEEK is 1-based
                
                return {
                    'most_common_time': f"{hour:02d}:00",
                    'most_common_day': day_name,
                    'pattern_strength': f"{most_common['frequency']} occurrences",
                    'patterns': patterns
                }
            else:
                return {
                    'most_common_time': 'No pattern',
                    'most_common_day': 'No pattern',
                    'pattern_strength': '0 occurrences'
                }
        except Exception as e:
            logger.warning(f"Temporal patterns query failed: {e}")
            return {'most_common_time': 'Unknown', 'most_common_day': 'Unknown'}

    def _extract_merchant_terms(self, description: str) -> List[str]:
        """Extract likely merchant/vendor names from description"""
        import re
        
        # Common words to ignore
        stop_words = {'at', 'in', 'on', 'the', 'and', 'or', 'for', 'with', 'from', 'to', 'by', 'purchase', 'payment', 'transaction'}
        
        # Clean and split description
        cleaned = re.sub(r'[^\w\s]', ' ', description.lower())
        words = [w.strip() for w in cleaned.split() if w.strip() and w not in stop_words and len(w) > 2]
        
        # Return first few meaningful words as potential merchant terms
        return words[:3] if words else []

# Global instance
db_analyzer = DatabaseTransactionAnalyzer()