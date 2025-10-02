"""
OpenAI-powered transaction analysis feedback generator
"""
import openai
import logging
from typing import Dict, List
import json
import os

logger = logging.getLogger(__name__)

class OpenAIFeedbackGenerator:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
    async def generate_transaction_feedback(self, transaction_data: Dict, database_analysis: Dict) -> Dict:
        """
        Generate intelligent feedback using OpenAI based on database analysis
        """
        try:
            # Prepare the analysis context for OpenAI
            context = self._prepare_analysis_context(transaction_data, database_analysis)
            
            # Create the prompt for OpenAI
            prompt = self._create_analysis_prompt(context)
            
            # Get response from OpenAI
            response = await self._call_openai_api(prompt)
            
            # Parse and structure the response
            return self._parse_openai_response(response, database_analysis)
            
        except Exception as e:
            logger.error(f"OpenAI feedback generation failed: {e}")
            return self._fallback_feedback(database_analysis)
    
    def _prepare_analysis_context(self, transaction_data: Dict, database_analysis: Dict) -> Dict:
        """Prepare structured context for OpenAI analysis"""
        return {
            'transaction': {
                'description': transaction_data.get('description', ''),
                'amount': transaction_data.get('amount', 0),
                'type': transaction_data.get('type', 'withdrawal')
            },
            'database_insights': {
                'suggested_category': database_analysis.get('category_patterns', {}).get('suggested_category', 'Unknown'),
                'category_confidence': database_analysis.get('category_patterns', {}).get('confidence', 0),
                'similar_transactions_count': len(database_analysis.get('similar_transactions', [])),
                'merchant_history': database_analysis.get('merchant_history', {}),
                'spending_patterns': database_analysis.get('spending_patterns', {}),
                'budget_impact': database_analysis.get('budget_impact', {}),
                'temporal_patterns': database_analysis.get('temporal_patterns', {})
            }
        }
    
    def _create_analysis_prompt(self, context: Dict) -> str:
        """Create a comprehensive prompt for OpenAI analysis"""
        transaction = context['transaction']
        insights = context['database_insights']
        
        prompt = f"""
You are a professional financial advisor analyzing a transaction using real database insights. Provide helpful, personalized feedback.

TRANSACTION DETAILS:
- Description: "{transaction['description']}"
- Amount: ${abs(transaction['amount']):.2f}
- Type: {transaction['type']}

DATABASE ANALYSIS RESULTS:
- Suggested Category: {insights['suggested_category']} (confidence: {insights['category_confidence']:.1%})
- Similar Transactions Found: {insights['similar_transactions_count']}
- Merchant History: {insights['merchant_history'].get('history', 'No history')}
- Amount Level: {insights['spending_patterns'].get('amount_level', 'unknown')}
- Budget Impact: {insights['budget_impact'].get('impact_level', 'unknown')}
- Common Transaction Time: {insights['temporal_patterns'].get('most_common_time', 'No pattern')}

Please provide a JSON response with these exact fields:
{{
    "categorization": {{
        "category": "recommended category name",
        "confidence": 0.85,
        "reasoning": "why this category was chosen based on database analysis"
    }},
    "spending_analysis": {{
        "amount_analysis": "high/normal/low",
        "transaction_frequency": "description of how often similar transactions occur",
        "budget_impact": "assessment of budget impact with specific insights"
    }},
    "pattern_recognition": {{
        "merchant_history": "analysis of merchant history and patterns",
        "spending_velocity": "analysis of spending frequency and timing",
        "anomaly_score": "low/medium/high with explanation"
    }},
    "recommendations": [
        "actionable recommendation 1 based on the data",
        "actionable recommendation 2 based on patterns",
        "actionable recommendation 3 for budget optimization"
    ],
    "insights": [
        "key insight 1 from database analysis",
        "key insight 2 about spending patterns",
        "key insight 3 about category trends"
    ]
}}

Focus on:
1. Using the database analysis to make accurate categorizations
2. Providing specific, actionable recommendations
3. Highlighting meaningful patterns from the user's actual transaction history
4. Being helpful and constructive, not judgmental

Respond only with valid JSON.
"""
        return prompt
    
    async def _call_openai_api(self, prompt: str) -> str:
        """Call OpenAI API with the analysis prompt"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a professional financial advisor providing transaction analysis. Always respond with valid JSON only."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise
    
    def _parse_openai_response(self, response: str, database_analysis: Dict) -> Dict:
        """Parse and validate OpenAI response"""
        try:
            parsed = json.loads(response)
            
            # Ensure required fields exist and add database data
            result = {
                'categorization': parsed.get('categorization', {
                    'category': database_analysis.get('category_patterns', {}).get('suggested_category', 'Uncategorized'),
                    'confidence': database_analysis.get('category_patterns', {}).get('confidence', 0.5),
                    'reasoning': 'Based on database analysis'
                }),
                'spending_analysis': parsed.get('spending_analysis', {}),
                'pattern_recognition': parsed.get('pattern_recognition', {}),
                'recommendations': parsed.get('recommendations', []),
                'insights': parsed.get('insights', []),
                'database_summary': {
                    'similar_transactions': len(database_analysis.get('similar_transactions', [])),
                    'merchant_frequency': database_analysis.get('merchant_history', {}).get('frequency', 0),
                    'spending_level': database_analysis.get('spending_patterns', {}).get('amount_level', 'unknown')
                }
            }
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response as JSON: {e}")
            return self._fallback_feedback(database_analysis)
        except Exception as e:
            logger.error(f"Error processing OpenAI response: {e}")
            return self._fallback_feedback(database_analysis)
    
    def _fallback_feedback(self, database_analysis: Dict) -> Dict:
        """Provide fallback feedback when OpenAI fails"""
        category_data = database_analysis.get('category_patterns', {})
        spending_data = database_analysis.get('spending_patterns', {})
        merchant_data = database_analysis.get('merchant_history', {})
        
        return {
            'categorization': {
                'category': category_data.get('suggested_category', 'Uncategorized'),
                'confidence': category_data.get('confidence', 0.5),
                'reasoning': category_data.get('reasoning', 'Based on database analysis')
            },
            'spending_analysis': {
                'amount_analysis': spending_data.get('amount_level', 'unknown'),
                'transaction_frequency': spending_data.get('transaction_frequency', 'Unknown frequency'),
                'budget_impact': spending_data.get('budget_impact', 'Impact unknown')
            },
            'pattern_recognition': {
                'merchant_history': merchant_data.get('history', 'No merchant history'),
                'spending_velocity': f"Based on {merchant_data.get('frequency', 0)} previous transactions",
                'anomaly_score': 'low'
            },
            'recommendations': [
                'Review your spending categories regularly',
                'Consider setting up budgets for frequent categories',
                'Track merchant spending patterns'
            ],
            'insights': [
                f"Category suggested based on {len(database_analysis.get('similar_transactions', []))} similar transactions",
                f"Spending level: {spending_data.get('amount_level', 'unknown')}",
                f"Merchant history: {merchant_data.get('history', 'first time')}"
            ]
        }

# Global instance
openai_feedback = OpenAIFeedbackGenerator()