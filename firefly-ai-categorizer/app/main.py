from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import httpx
from app.ai_model import predict_category, retrain_model
from app.feedback_storage import save_feedback
import dotenv, os
app = FastAPI()
dotenv.load_dotenv()
FIREFFLY_API = "http://app:8080/api/v1"
FIREFFLY_TOKEN = os.environ.get("FIREFLY_TOKEN", "your_firefly_token")
HEADERS = {"Authorization": f"Bearer {FIREFFLY_TOKEN}"}


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker."""
    try:
        # Check if model exists and is loadable
        from app.ai_model import get_model_path
        model_status = "available"
        try:
            get_model_path()
        except:
            model_status = "not_available"
        
        return {
            "status": "healthy",
            "model_status": model_status
        }
    except Exception as e:
        return {
            "status": "healthy",  # Still healthy even without model
            "model_status": "unknown",
            "detail": str(e)
        }

@app.post("/incoming")
async def incoming_event(request: Request):
    data = await request.json()
    if "content" not in data or "transactions" not in data["content"]:
        return JSONResponse(status_code=400, content={"status": "error", "detail": "Missing content or transactions in payload"})

    transactions = data["content"]["transactions"]
    if not transactions or "transaction_journal_id" not in transactions[0] or "description" not in transactions[0]:
        return JSONResponse(status_code=400, content={"status": "error", "detail": "Missing transaction_journal_id or description in payload"})

    tx_id = transactions[0]["transaction_journal_id"]
    tx_desc = transactions[0]["description"]

    try:
        ai_category = predict_category(tx_desc)
        
        # Get confidence from prediction if available
        confidence = 0.85  # Default confidence for successful predictions
        
    except Exception as e:
        print(f"No model available")
        return JSONResponse(status_code=200, content={"status": "no_model", "category": "Uncategorized", "detail": str(e)})

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{FIREFFLY_API}/categories", headers=HEADERS)
            if resp.status_code != 200:
                return JSONResponse(status_code=500, content={"status": "error", "detail": f"Failed to fetch categories: {resp.status_code}"})
            
            categories = resp.json()["data"]
        except Exception as e:
            return JSONResponse(status_code=500, content={"status": "error", "detail": f"API communication error: {str(e)}"})

        # Find or create category
        category_id = None
        for cat in categories:
            if cat["attributes"]["name"].lower() == ai_category.lower():
                category_id = cat["id"]
                break

        if not category_id:
            try:
                create = await client.post(
                    f"{FIREFFLY_API}/categories",
                    headers=HEADERS,
                    json={"name": ai_category}
                )
                if create.status_code == 200:
                    category_id = create.json()["data"]["id"]
                else:
                    return JSONResponse(status_code=500, content={"status": "error", "detail": f"Failed to create category: {create.status_code}"})
            except Exception as e:
                return JSONResponse(status_code=500, content={"status": "error", "detail": f"Failed to create category: {str(e)}"})

        # Update the transaction to assign it to the category
        try:
            update_payload = {
                "apply_rules": False,
                "fire_webhooks": False,  # Prevent infinite webhook loops
                "transactions": [{
                    "category_id": category_id
                }]
            }
            
            attach_resp = await client.put(
                f"{FIREFFLY_API}/transactions/{tx_id}",
                headers=HEADERS,
                json=update_payload
            )
            if attach_resp.status_code not in [200, 201, 204]:
                return JSONResponse(status_code=500, content={"status": "error", "detail": f"Failed to update transaction: {attach_resp.status_code}, response: {attach_resp.text}"})
        except Exception as e:
            return JSONResponse(status_code=500, content={"status": "error", "detail": f"Failed to update transaction: {str(e)}"})

    return {"status": "AI category assigned", "category": ai_category, "confidence": confidence}



@app.post("/feedback")
async def transaction_updated(request: Request):
    data = await request.json()
    tx_desc = data["transactions"][0]["description"]
    user_cat = data["transactions"][0]["category_name"]

    save_feedback(tx_desc, user_cat)
    retrain_model()  # optional: retrain immediately

    return {"status": "Feedback stored", "category": user_cat}
