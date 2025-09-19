# webhook_service/main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Set up logging
LOG_DIR = Path("/app/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "webhook_service.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Firefly III Webhook Service")

# Allow CORS (if needed for external testing)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker."""
    return {"status": "healthy"}

# Configuration from environment
FIREFLY_API_URL = os.environ.get("FIREFLY_API_URL", "http://firefly-app:8000")
FIREFLY_TOKEN = os.environ.get("FIREFLY_TOKEN")
AI_SERVICE_URL = os.environ.get("AI_SERVICE_URL", "http://ai-service:8000")

if not FIREFLY_TOKEN:
    raise ValueError("FIREFLY_TOKEN environment variable must be set")

headers = {
    "Authorization": f"Bearer {FIREFLY_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

async def get_transaction_details(tx_id: str) -> Dict[str, Any]:
    """Fetch full transaction details from Firefly III."""
    try:
        async with httpx.AsyncClient() as client:
            tx_res = await client.get(
                f"{FIREFLY_API_URL}/api/v1/transactions/{tx_id}",
                headers=headers
            )
        if tx_res.status_code != 200:
            raise HTTPException(status_code=tx_res.status_code, detail="Failed to fetch transaction")
        return tx_res.json()["data"]
    except Exception as e:
        logger.error(f"Error fetching transaction {tx_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch transaction: {str(e)}")

async def get_category_prediction(description: str, transaction_id: str = None) -> Dict[str, Any]:
    """Get category prediction from AI service."""
    try:
        # Build payload as expected by AI categorizer
        payload = {
            "content": {
                "transactions": [
                    {
                        "transaction_journal_id": transaction_id or "dummy_id",
                        "description": description
                    }
                ]
            }
        }
        async with httpx.AsyncClient() as client:
            ai_res = await client.post(
                f"{AI_SERVICE_URL}/incoming",
                json=payload,
                headers={"Accept": "application/json"}
            )
        if ai_res.status_code != 200:
            raise HTTPException(status_code=ai_res.status_code, detail="AI service error")
        result = ai_res.json()
        logger.info(f"AI prediction: {result}")
        return result
    except Exception as e:
        logger.error(f"Error getting prediction for '{description}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")

async def get_or_create_category(category: str) -> str:
    """Get category ID by name or create if it doesn't exist."""
    try:
        # First try to find existing category
        async with httpx.AsyncClient() as client:
            cats_res = await client.get(
                f"{FIREFLY_API_URL}/api/v1/categories",
                headers=headers
            )
            
        if cats_res.status_code != 200:
            raise HTTPException(status_code=cats_res.status_code, detail="Failed to fetch categories")
            
        cats = cats_res.json()["data"]
        for cat in cats:
            if cat["attributes"]["name"].lower() == category.lower():
                return cat["id"]
                
        # Category not found, create it
        logger.info(f"Creating new category: {category}")
        async with httpx.AsyncClient() as client:
            create_res = await client.post(
                f"{FIREFLY_API_URL}/api/v1/categories",
                headers=headers,
                json={"name": category}
            )
        if create_res.status_code != 200:
            raise HTTPException(status_code=create_res.status_code, detail="Failed to create category")
            
        return create_res.json()["data"]["id"]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error managing category '{category}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Category management failed: {str(e)}")

@app.post("/webhook")
async def handle_webhook(req: Request):
    """Handle incoming webhooks from Firefly III."""
    try:
        data = await req.json()
        logger.info(f"Received webhook: {data.get('trigger')}")
        logger.info(f"Full webhook payload: {data}")

        # Verify this is a transaction creation event
        if data.get("trigger") not in ["TRIGGER_STORE_TRANSACTION", "STORE_TRANSACTION"]:
            logger.info(f"Ignoring non-transaction trigger: {data.get('trigger')}")
            return {"status": "ignored", "reason": "not a transaction event"}

        content = data.get("content", {})
        
        # Get transaction details from webhook payload
        transactions = content.get('transactions', [])
        if not transactions:
            logger.error("No transactions in webhook data")
            raise HTTPException(status_code=400, detail="No transactions found")
            
        transaction = transactions[0]
        tx_id = transaction.get("transaction_journal_id")
        desc = transaction.get('description', "")
        
        if not tx_id:
            logger.error("No transaction journal ID in webhook data")
            raise HTTPException(status_code=400, detail="No transaction journal ID found")
            
        if not desc:
            logger.warning(f"Transaction {tx_id} has no description")
            return {"status": "ignored", "reason": "no description"}

        # Get AI prediction
        prediction = await get_category_prediction(desc, tx_id)
        
        # Handle case where AI service has no model
        if prediction.get("status") == "no_model":
            logger.info(f"AI service has no model available, skipping categorization for transaction {tx_id}")
            return {
                "status": "no_model_available",
                "reason": "AI service has no trained model"
            }
            
        category = prediction.get("category", "Uncategorized")
        confidence = prediction.get("confidence", 0.0)

        # Skip if confidence is too low
        if confidence < 0.3:  # Lowered threshold for better acceptance
            logger.info(f"Skipping low confidence prediction ({confidence:.2f}) for transaction {tx_id}")
            return {
                "status": "ignored",
                "reason": "low confidence",
                "confidence": confidence
            }

        # Get or create category
        cat_id = await get_or_create_category(category)

        # Update transaction with new category
        update_payload = {
            "apply_rules": False,
            "fire_webhooks": False,
            "transactions": [{
                "category_id": cat_id
            }]
        }
        async with httpx.AsyncClient() as client:
            upd_res = await client.put(
                f"{FIREFLY_API_URL}/api/v1/transactions/{tx_id}",
                json=update_payload,
                headers=headers
            )
        if upd_res.status_code not in (200, 204):
            raise HTTPException(status_code=upd_res.status_code, detail="Failed to update transaction")

        logger.info(f"Updated transaction {tx_id} with category {category} (confidence: {confidence:.2f})")
        return {
            "status": "category_updated",
            "transaction_id": tx_id,
            "category": category,
            "confidence": confidence
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")

@app.post("/feedback")
async def handle_feedback(req: Request):
    """Handle manual category changes for AI model improvement."""
    try:
        data = await req.json()
        tx_id = data.get("transaction_id")
        if not tx_id:
            raise HTTPException(status_code=400, detail="No transaction ID provided")

        # Get transaction details
        tx_data = await get_transaction_details(tx_id)
        desc = tx_data["attributes"].get("description", "")
        category = tx_data["attributes"].get("category_name")
        
        if not desc or not category:
            return {"status": "ignored", "reason": "missing data"}

        # Send feedback to AI service
        try:
            async with httpx.AsyncClient() as client:
                feedback_res = await client.post(
                    f"{AI_SERVICE_URL}/feedback",
                    json={
                        "description": desc,
                        "category": category
                    }
                )
            if feedback_res.status_code == 200:
                logger.info(f"Sent feedback for transaction {tx_id}")
                return {"status": "feedback_sent"}
            else:
                logger.warning(f"Failed to send feedback: {feedback_res.status_code}")
                return {"status": "feedback_failed", "error": feedback_res.text}
        except Exception as e:
            logger.error(f"Error sending feedback: {str(e)}")
            return {"status": "feedback_failed", "error": str(e)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Feedback processing failed: {str(e)}")
