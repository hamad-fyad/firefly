from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import httpx
import logging
import time
from app.ai_model import predict_category, retrain_model
from app.feedback_storage import save_feedback
from app.model_metrics import get_model_performance_summary, get_predictions_data, initialize_metrics_storage
import dotenv, os

# Set up logging
logger = logging.getLogger(__name__)
app = FastAPI()
dotenv.load_dotenv()

# Initialize database and metrics storage on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and metrics storage on application startup."""
    logger.info("🚀 Initializing AI Categorizer service...")
    
    # Check environment variables
    import os
    openai_key = os.getenv("OPENAI_API_KEY")
    firefly_token = os.getenv("FIREFLY_TOKEN")
    
    if openai_key:
        key_preview = f"{openai_key[:4]}...{openai_key[-4:]}" if len(openai_key) > 8 else "[short_key]"
        logger.info(f"✅ OpenAI API key found: {key_preview} (length: {len(openai_key)})")
        if not openai_key.startswith("sk-"):
            logger.warning("⚠️ OpenAI API key should start with 'sk-'")
    else:
        logger.error("❌ OPENAI_API_KEY not found in environment")
    
    if firefly_token:
        token_preview = f"{firefly_token[:8]}...{firefly_token[-4:]}" if len(firefly_token) > 12 else "[short_token]"
        logger.info(f"✅ Firefly token found: {token_preview} (length: {len(firefly_token)})")
    else:
        logger.error("❌ FIREFLY_TOKEN not found in environment")
    
    logger.info(f"🔗 Firefly API endpoint: {FIREFFLY_API}")
    
    # Test OpenAI client
    try:
        from app.ai_model import get_openai_client
        client = get_openai_client()
        if client:
            logger.info("✅ OpenAI client initialized successfully")
        else:
            logger.warning("⚠️ OpenAI client initialization failed")
    except Exception as openai_error:
        logger.error(f"❌ OpenAI client error: {str(openai_error)}")
    
    try:
        # Initialize metrics storage (will try database first, fallback to file)
        initialize_metrics_storage()
        logger.info("✅ Metrics storage initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize metrics storage: {str(e)}")
        logger.info("⚠️ Service will continue with limited functionality")
    
    logger.info("🎉 AI Categorizer service startup complete")
    logger.info("💡 Use /test-ai endpoint to test ChatGPT integration")
    logger.info("🔍 Use /debug-env endpoint to check environment configuration")
FIREFFLY_API = "http://app:8080/api/v1"
FIREFFLY_TOKEN = os.environ.get("FIREFLY_TOKEN")
HEADERS = {"Authorization": f"Bearer {FIREFFLY_TOKEN}"}


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker."""
    try:
        from app.ai_model import get_openai_client
        client = get_openai_client()
        
        if client:
            # Test if OpenAI is actually working (not just configured)
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=5,
                    timeout=3
                )
                model_status = "available"
                model_type = "openai"
            except Exception as openai_error:
                # OpenAI configured but not working (quota/network issues)
                if "insufficient_quota" in str(openai_error) or "429" in str(openai_error):
                    model_status = "quota_exceeded"
                    model_type = "fallback_active"
                else:
                    model_status = "error"
                    model_type = "fallback_active"
        else:
            model_status = "fallback"
            model_type = "keywords"
            
        # Check database status
        database_status = "unknown"
        try:
            from app.database import test_connection
            if test_connection():
                database_status = "available"
            else:
                database_status = "unavailable"
        except Exception as db_error:
            database_status = "error"
            
        return {
            "status": "healthy", 
            "model_status": model_status, 
            "model_type": model_type,
            "database_status": database_status,
            "storage_mode": "database" if database_status == "available" else "file"
        }
        
    except Exception as e:
        return {
            "status": "healthy",  # Still healthy even without model/database
            "model_status": "error",
            "database_status": "error",
            "detail": str(e)
        }

@app.post("/incoming")
async def incoming_event(request: Request):
    logger.info("🔄 Received new transaction for categorization")
    
    try:
        data = await request.json()
        logger.debug(f"📥 Incoming payload keys: {list(data.keys())}")
    except Exception as json_error:
        logger.error(f"❌ Failed to parse JSON payload: {str(json_error)}")
        return JSONResponse(status_code=400, content={"status": "error", "detail": "Invalid JSON payload"})
    
    if "content" not in data or "transactions" not in data["content"]:
        logger.error("❌ Missing 'content' or 'transactions' in payload")
        logger.debug(f"🔍 Available payload structure: {data}")
        return JSONResponse(status_code=400, content={"status": "error", "detail": "Missing content or transactions in payload"})

    transactions = data["content"]["transactions"]
    logger.info(f"📊 Processing {len(transactions)} transaction(s)")
    
    if not transactions or "transaction_journal_id" not in transactions[0] or "description" not in transactions[0]:
        logger.error("❌ Missing transaction_journal_id or description in first transaction")
        logger.debug(f"🔍 Transaction structure: {transactions[0] if transactions else 'No transactions'}")
        return JSONResponse(status_code=400, content={"status": "error", "detail": "Missing transaction_journal_id or description in payload"})

    tx_id = transactions[0]["transaction_journal_id"]
    tx_desc = transactions[0]["description"]
    
    logger.info(f"🏷️ Processing transaction {tx_id}: '{tx_desc}'")

    # AI Categorization with detailed logging
    logger.info("🤖 Starting AI categorization process")
    categorization_start = time.time()
    
    try:
        ai_category = predict_category(tx_desc)
        categorization_time = time.time() - categorization_start
        confidence = 0.85  # Default confidence for successful predictions
        
        logger.info(f"✅ AI categorization completed in {categorization_time:.2f}s")
        logger.info(f"🎯 Result: '{tx_desc}' -> '{ai_category}' (confidence: {confidence})")
        
    except Exception as ai_error:
        categorization_time = time.time() - categorization_start
        logger.error(f"❌ AI categorization failed after {categorization_time:.2f}s: {str(ai_error)}")
        ai_category = "Uncategorized"
        confidence = 0.5
        logger.warning(f"🔄 Using fallback category: '{ai_category}'")
        
        # IMPORTANT: Record the fallback prediction in metrics since predict_category() failed
        try:
            from app.model_metrics import record_prediction
            from app import model_manager
            
            # Get current model version for metrics
            try:
                metadata = model_manager.load_metadata()
                current_version = metadata.get("current_version", "fallback-error-v1") if metadata else "fallback-error-v1"
            except Exception:
                current_version = "fallback-error-v1"
            
            # Record the fallback prediction
            record_prediction(
                version_id=current_version,
                description=tx_desc,
                predicted_category=ai_category,
                confidence=confidence
            )
            logger.info(f"📊 Recorded fallback prediction metrics: '{tx_desc}' -> '{ai_category}' (confidence: {confidence})")
            
        except Exception as metrics_error:
            logger.error(f"❌ Failed to record fallback prediction metrics: {str(metrics_error)}")
            logger.warning("🔍 This may explain why metrics don't show for failed predictions")    # Firefly III Integration
    logger.info("🔗 Connecting to Firefly III API")
    firefly_start = time.time()
    
    async with httpx.AsyncClient() as client:
        try:
            logger.debug(f"📡 Fetching categories from: {FIREFFLY_API}/categories")
            resp = await client.get(f"{FIREFFLY_API}/categories", headers=HEADERS)
            firefly_time = time.time() - firefly_start
            
            logger.info(f"📡 Firefly API response: {resp.status_code} in {firefly_time:.2f}s")
            
            if resp.status_code == 302:
                logger.error("🔐 Firefly III authentication failed (302 redirect) - Token expired/invalid")
                logger.warning("💡 Check FIREFLY_TOKEN environment variable")
                return {
                    "status": "AI category predicted (auth required)", 
                    "category": ai_category, 
                    "confidence": confidence,
                    "message": "Category predicted but Firefly III requires re-authentication. Please check/update the API token."
                }
            elif resp.status_code == 401:
                logger.error("🚫 Firefly III unauthorized (401) - Invalid token")
                return {
                    "status": "AI category predicted (unauthorized)", 
                    "category": ai_category, 
                    "confidence": confidence,
                    "message": "Invalid Firefly III API token"
                }
            elif resp.status_code != 200:
                logger.error(f"❌ Firefly III API error {resp.status_code}: {resp.text[:200]}")
                return {
                    "status": "AI category predicted (API error)", 
                    "category": ai_category, 
                    "confidence": confidence,
                    "message": f"Category predicted but Firefly III API returned {resp.status_code}"
                }
            
            categories = resp.json()["data"]
        except Exception as e:
            print(f"⚠️  Firefly III connection error: {str(e)}. Category '{ai_category}' predicted but not applied.")
            return {
                "status": "AI category predicted (connection error)", 
                "category": ai_category, 
                "confidence": confidence,
                "message": f"Category predicted but connection to Firefly III failed: {str(e)}"
            }

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
                if create.status_code in [200, 201]:
                    category_id = create.json()["data"]["id"]
                    print(f"✅ Created new category '{ai_category}' with ID {category_id}")
                else:
                    print(f"⚠️  Failed to create category '{ai_category}' (status {create.status_code})")
                    return {
                        "status": "AI category predicted (category creation failed)", 
                        "category": ai_category, 
                        "confidence": confidence,
                        "message": f"Category predicted but creation failed with status {create.status_code}"
                    }
            except Exception as e:
                print(f"⚠️  Exception creating category '{ai_category}': {str(e)}")
                return {
                    "status": "AI category predicted (category creation error)", 
                    "category": ai_category, 
                    "confidence": confidence,
                    "message": f"Category predicted but creation failed: {str(e)}"
                }

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
            if attach_resp.status_code in [200, 201, 204]:
                print(f"✅ Transaction {tx_id} successfully categorized as '{ai_category}'")
                return {"status": "AI category assigned", "category": ai_category, "confidence": confidence}
            else:
                print(f"⚠️  Failed to update transaction {tx_id} (status {attach_resp.status_code})")
                return {
                    "status": "AI category predicted (assignment failed)", 
                    "category": ai_category, 
                    "confidence": confidence,
                    "message": f"Category predicted but assignment failed with status {attach_resp.status_code}"
                }
        except Exception as e:
            print(f"⚠️  Exception updating transaction {tx_id}: {str(e)}")
            return {
                "status": "AI category predicted (assignment error)", 
                "category": ai_category, 
                "confidence": confidence,
                "message": f"Category predicted but assignment failed: {str(e)}"
            }

    return {"status": "AI category assigned", "category": ai_category, "confidence": confidence}



@app.post("/feedback")
async def transaction_updated(request: Request):
    """Enhanced feedback endpoint that records accuracy data for confidence improvement."""
    try:
        data = await request.json()
        tx_desc = data["transactions"][0]["description"]
        user_cat = data["transactions"][0]["category_name"]
        predicted_cat = data.get("predicted_category")  # If available
        confidence = data.get("confidence", 0.7)  # If available

        # Store traditional feedback
        save_feedback(tx_desc, user_cat)
        
        # Record accuracy feedback if we have prediction info
        if predicted_cat:
            from . import model_metrics
            # Find the most recent prediction for this description
            recent_predictions = model_metrics.get_recent_predictions(limit=100)
            prediction_id = None
            
            for pred in recent_predictions:
                if pred["description"].strip().lower() == tx_desc.strip().lower():
                    prediction_id = pred.get("id", len(recent_predictions))  # Use ID or fallback
                    break
            
            if prediction_id:
                model_metrics.record_accuracy_feedback(
                    prediction_id=prediction_id,
                    predicted_category=predicted_cat,
                    actual_category=user_cat,
                    description=tx_desc,
                    confidence=confidence,
                    feedback_source="user"
                )
                logger.info(f"Recorded accuracy feedback: '{predicted_cat}' -> '{user_cat}' for '{tx_desc}'")
        
        # Optional: retrain model (can be disabled for performance)
        # retrain_model()

        return {
            "status": "Feedback stored", 
            "category": user_cat,
            "accuracy_recorded": predicted_cat is not None
        }
    except Exception as e:
        logger.error(f"Error processing feedback: {str(e)}")
        return {"status": "Error", "message": str(e)}


@app.post("/test-categorize")
async def test_categorize(request: Request):
    """Test endpoint for manual categorization testing."""
    data = await request.json()
    description = data.get("description", "")
    
    if not description:
        return JSONResponse(status_code=400, content={"error": "Description required"})
    
    try:
        category = predict_category(description)
        return {"description": description, "predicted_category": category, "source": "ai_service"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/metrics", response_class=HTMLResponse)
async def metrics_dashboard():
    """Serve the metrics dashboard UI."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Categorizer - Metrics Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                height: 100vh;
                padding: 20px;
                overflow-x: hidden;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                padding: 30px;
                max-height: calc(100vh - 40px);
                overflow-y: auto;
            }
            
            .header {
                text-align: center;
                margin-bottom: 30px;
                color: #333;
            }
            
            .header h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
                background: linear-gradient(45deg, #667eea, #764ba2);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            
            .stat-card {
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 0 8px 20px rgba(0,0,0,0.1);
                transition: transform 0.3s ease;
            }
            
            .stat-card:hover {
                transform: translateY(-5px);
            }
            
            .stat-card h3 {
                font-size: 2.5em;
                margin-bottom: 5px;
            }
            
            .stat-card p {
                font-size: 1.1em;
                opacity: 0.9;
            }
            
            .charts-section {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 30px;
                margin-bottom: 30px;
            }
            
            .chart-container {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.08);
                height: 400px;
            }
            
            .chart-container canvas {
                max-height: 300px !important;
            }
            
            .chart-container h3 {
                margin-bottom: 15px;
                color: #333;
                text-align: center;
            }
            
            .predictions-table {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            }
            
            .predictions-table h3 {
                margin-bottom: 15px;
                color: #333;
                text-align: center;
            }
            
            table {
                width: 100%;
                border-collapse: collapse;
                background: white;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 3px 10px rgba(0,0,0,0.1);
            }
            
            th, td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #eee;
            }
            
            th {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                font-weight: 600;
            }
            
            tr:hover {
                background-color: #f5f5f5;
            }
            
            .confidence-bar {
                background: #e0e0e0;
                border-radius: 10px;
                height: 8px;
                overflow: hidden;
            }
            
            .confidence-fill {
                height: 100%;
                background: linear-gradient(90deg, #f093fb, #f5576c);
                border-radius: 10px;
                transition: width 0.3s ease;
            }
            
            .refresh-btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 25px;
                cursor: pointer;
                font-size: 1em;
                font-weight: 600;
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
                transition: all 0.3s ease;
                margin-bottom: 20px;
            }
            
            .refresh-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(0,0,0,0.3);
            }
            
            .loading {
                text-align: center;
                color: #666;
                font-style: italic;
            }
            
            @media (max-width: 768px) {
                .charts-section {
                    grid-template-columns: 1fr;
                }
                
                .stats-grid {
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 AI Categorizer Dashboard</h1>
                <p>Real-time performance metrics for transaction categorization</p>
            </div>
            
            <button class="refresh-btn" onclick="refreshMetrics()">🔄 Refresh Data</button>
            
            <div class="stats-grid" id="statsGrid">
                <div class="loading">Loading metrics...</div>
            </div>
            
            <div class="charts-section">
                <div class="chart-container">
                    <h3>📊 Category Distribution</h3>
                    <canvas id="categoryChart" width="400" height="300"></canvas>
                </div>
                <div class="chart-container">
                    <h3>📈 Predictions Over Time</h3>
                    <canvas id="timeChart" width="400" height="300"></canvas>
                </div>
            </div>
            
            <div class="predictions-table">
                <h3>📝 Recent Predictions</h3>
                <div id="predictionsTable">
                    <div class="loading">Loading predictions...</div>
                </div>
            </div>
        </div>
        
        <script>
            let categoryChart, timeChart;
            
            async function fetchMetrics() {
                try {
                    const response = await fetch('/api/metrics');
                    return await response.json();
                } catch (error) {
                    console.error('Error fetching metrics:', error);
                    return null;
                }
            }
            
            function updateStats(data) {
                const statsGrid = document.getElementById('statsGrid');
                const summary = data.summary;
                const predictions = data.predictions;
                const accuracy = data.accuracy || {};
                
                // Use real-time accuracy if available, otherwise fall back to model accuracy
                const realAccuracy = accuracy.overall_accuracy || summary.average_metrics.accuracy;
                const accuracySource = accuracy.sample_size > 0 ? "Real-time" : "Estimated";
                
                statsGrid.innerHTML = `
                    <div class="stat-card">
                        <h3>${summary.prediction_stats.total_predictions}</h3>
                        <p>Total Predictions</p>
                    </div>
                    <div class="stat-card">
                        <h3>${summary.prediction_stats.unique_categories}</h3>
                        <p>Unique Categories</p>
                    </div>
                    <div class="stat-card">
                        <h3>${(summary.prediction_stats.avg_confidence * 100).toFixed(1)}%</h3>
                        <p>Avg Confidence</p>
                    </div>
                    <div class="stat-card" title="${accuracySource} accuracy based on ${accuracy.sample_size || 0} feedback entries">
                        <h3 style="color: ${accuracy.sample_size > 0 ? '#4CAF50' : '#FF9800'}">${(realAccuracy * 100).toFixed(1)}%</h3>
                        <p>${accuracySource} Accuracy</p>
                        <small style="color: #666;">${accuracy.sample_size || 0} feedback entries</small>
                    </div>
                `;
            }
            
            function updateCategoryChart(predictions) {
                const categories = {};
                predictions.forEach(pred => {
                    categories[pred.predicted_category] = (categories[pred.predicted_category] || 0) + 1;
                });
                
                const labels = Object.keys(categories);
                const data = Object.values(categories);
                const colors = [
                    '#ff6384', '#36a2eb', '#cc65fe', '#ffce56', '#fd6c6c',
                    '#4bc0c0', '#9966ff', '#ff9f40', '#ff6384', '#c9cbcf'
                ];
                
                if (categoryChart) {
                    categoryChart.destroy();
                }
                
                const ctx = document.getElementById('categoryChart').getContext('2d');
                categoryChart = new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: labels,
                        datasets: [{
                            data: data,
                            backgroundColor: colors.slice(0, labels.length),
                            borderWidth: 0
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom'
                            }
                        }
                    }
                });
            }
            
            function updateTimeChart(predictions) {
                const last30Days = predictions.slice(-30);
                const dates = last30Days.map(p => new Date(p.timestamp).toLocaleDateString());
                const confidences = last30Days.map(p => p.confidence * 100);
                
                if (timeChart) {
                    timeChart.destroy();
                }
                
                const ctx = document.getElementById('timeChart').getContext('2d');
                timeChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: dates,
                        datasets: [{
                            label: 'Confidence %',
                            data: confidences,
                            borderColor: '#667eea',
                            backgroundColor: 'rgba(102, 126, 234, 0.1)',
                            fill: true,
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                max: 100
                            }
                        }
                    }
                });
            }
            
            function updatePredictionsTable(predictions) {
                const tableDiv = document.getElementById('predictionsTable');
                const recent = predictions.slice(-10).reverse();
                
                tableDiv.innerHTML = `
                    <table>
                        <thead>
                            <tr>
                                <th>Description</th>
                                <th>Category</th>
                                <th>Confidence</th>
                                <th>Time</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${recent.map(pred => `
                                <tr>
                                    <td>${pred.description}</td>
                                    <td><strong>${pred.predicted_category}</strong></td>
                                    <td>
                                        <div class="confidence-bar">
                                            <div class="confidence-fill" style="width: ${pred.confidence * 100}%"></div>
                                        </div>
                                        ${(pred.confidence * 100).toFixed(1)}%
                                    </td>
                                    <td>${new Date(pred.timestamp).toLocaleString()}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;
            }
            
            async function refreshMetrics() {
                const data = await fetchMetrics();
                if (data) {
                    updateStats(data);
                    updateCategoryChart(data.predictions);
                    updateTimeChart(data.predictions);
                    updatePredictionsTable(data.predictions);
                }
            }
            
            // Load data on page load
            document.addEventListener('DOMContentLoaded', refreshMetrics);
            
            // Auto-refresh every 30 seconds
            setInterval(refreshMetrics, 30000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/api/accuracy")
async def get_real_time_accuracy():
    """API endpoint to get real-time accuracy metrics based on user feedback."""
    try:
        from . import model_metrics
        accuracy_data = model_metrics.get_real_time_accuracy()
        return {
            "status": "success",
            "data": accuracy_data,
            "timestamp": model_metrics.datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting real-time accuracy: {str(e)}")
        return {
            "status": "error", 
            "message": str(e),
            "data": {"overall_accuracy": 0.75, "sample_size": 0}
        }

@app.get("/api/metrics")
async def get_metrics_data():
    """API endpoint to get metrics data in JSON format."""
    try:
        summary = get_model_performance_summary()
        predictions = get_predictions_data()
        
        # Get real-time accuracy data
        from . import model_metrics
        accuracy_data = model_metrics.get_real_time_accuracy()
        
        return {
            "summary": summary,
            "predictions": predictions,
            "accuracy": accuracy_data,
            "storage_type": summary.get("storage_type", "unknown")
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to load metrics: {str(e)}"}
        )

@app.post("/test-ai")
async def test_ai_categorization(request: Request):
    """
    Test endpoint for diagnosing ChatGPT/OpenAI integration issues.
    Use this to test AI categorization with detailed logging.
    """
    try:
        data = await request.json()
        test_description = data.get("description", "Test transaction from Starbucks")
        
        logger.info(f"🧪 TEST: Starting AI categorization test with: '{test_description}'")
        
        # Test OpenAI client first
        from app.ai_model import get_openai_client
        client = get_openai_client()
        
        if not client:
            logger.error("🚨 TEST FAILED: OpenAI client is None")
            return {
                "status": "test_failed",
                "error": "OpenAI client initialization failed",
                "suggestions": [
                    "Check OPENAI_API_KEY environment variable",
                    "Verify API key is valid",
                    "Check network connectivity"
                ]
            }
        
        logger.info("✅ TEST: OpenAI client initialized successfully")
        
        # Test categorization
        start_time = time.time()
        try:
            category = predict_category(test_description)
            duration = time.time() - start_time
            
            logger.info(f"✅ TEST: AI categorization successful in {duration:.2f}s")
            
            return {
                "status": "test_passed",
                "input_description": test_description,
                "predicted_category": category,
                "duration_seconds": duration,
                "openai_client_status": "working",
                "message": "ChatGPT integration is working properly"
            }
            
        except Exception as prediction_error:
            duration = time.time() - start_time
            logger.error(f"🚨 TEST FAILED: Prediction error after {duration:.2f}s: {str(prediction_error)}")
            
            return {
                "status": "test_failed",
                "error": str(prediction_error),
                "duration_seconds": duration,
                "openai_client_status": "initialized_but_failed",
                "suggestions": [
                    "Check OpenAI API quota/billing",
                    "Verify internet connectivity",
                    "Check for API rate limits",
                    "Review error logs for details"
                ]
            }
            
    except Exception as e:
        logger.error(f"🚨 TEST ENDPOINT ERROR: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "test_error",
                "error": str(e),
                "message": "Test endpoint itself failed"
            }
        )

@app.get("/debug-env")
async def debug_environment():
    """Debug endpoint to check environment configuration (without exposing secrets)."""
    import os
    from pathlib import Path
    
    # Check environment variables (safely)
    openai_key_set = bool(os.getenv("OPENAI_API_KEY"))
    firefly_token_set = bool(os.getenv("FIREFLY_TOKEN"))
    
    # Get key lengths for verification (without exposing actual keys)
    openai_key_len = len(os.getenv("OPENAI_API_KEY", "")) if openai_key_set else 0
    firefly_token_len = len(os.getenv("FIREFLY_TOKEN", "")) if firefly_token_set else 0
    
    # Check metrics storage
    metrics_info = {}
    try:
        from app.model_metrics import METRICS_FILE, DATABASE_AVAILABLE
        from app.database import test_connection
        
        # Database status
        db_connected = test_connection() if DATABASE_AVAILABLE else False
        
        # File storage status
        metrics_file_exists = METRICS_FILE.exists()
        metrics_file_size = METRICS_FILE.stat().st_size if metrics_file_exists else 0
        
        # Load current metrics count
        if metrics_file_exists:
            try:
                import json
                with open(METRICS_FILE, 'r') as f:
                    metrics_data = json.load(f)
                predictions_count = len(metrics_data.get("predictions", []))
                models_count = len(metrics_data.get("models", []))
            except Exception:
                predictions_count = "error"
                models_count = "error"
        else:
            predictions_count = 0
            models_count = 0
        
        metrics_info = {
            "database_available": DATABASE_AVAILABLE,
            "database_connected": db_connected,
            "storage_mode": "database" if (DATABASE_AVAILABLE and db_connected) else "file",
            "metrics_file_path": str(METRICS_FILE),
            "metrics_file_exists": metrics_file_exists,
            "metrics_file_size_bytes": metrics_file_size,
            "predictions_count": predictions_count,
            "models_count": models_count
        }
    except Exception as e:
        metrics_info = {"error": str(e)}
    
    return {
        "environment_check": {
            "openai_api_key_set": openai_key_set,
            "openai_key_length": openai_key_len,
            "firefly_token_set": firefly_token_set,
            "firefly_token_length": firefly_token_len,
        },
        "api_endpoints": {
            "firefly_api": FIREFFLY_API,
        },
        "metrics_storage": metrics_info,
        "suggestions": {
            "openai_key": "Should be 51+ characters starting with 'sk-'" if openai_key_set else "Set OPENAI_API_KEY environment variable",
            "firefly_token": "Should be 64+ characters" if firefly_token_set else "Set FIREFLY_TOKEN environment variable"
        },
        "test_commands": {
            "test_ai": "POST /test-ai with {'description': 'test transaction'}",
            "health_check": "GET /health",
            "metrics": "GET /api/metrics",
            "debug_env": "GET /debug-env (this endpoint)"
        }
    }