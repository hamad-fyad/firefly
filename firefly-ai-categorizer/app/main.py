from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import httpx
from app.ai_model import predict_category, retrain_model
from app.feedback_storage import save_feedback
from app.model_metrics import get_model_performance_summary, get_predictions_data
import dotenv, os
app = FastAPI()
dotenv.load_dotenv()
FIREFFLY_API = "http://app:8080/api/v1"
# Use FIREFLY_TOKEN2 if available, fallback to FIREFLY_TOKEN
FIREFFLY_TOKEN = os.environ.get("FIREFLY_TOKEN2", os.environ.get("FIREFLY_TOKEN", "your_firefly_token"))
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
            
        return {"status": "healthy", "model_status": model_status, "model_type": model_type}
        
    except Exception as e:
        return {
            "status": "healthy",  # Still healthy even without model
            "model_status": "error",
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

    # predict_category now handles all fallbacks internally and never raises exceptions
    ai_category = predict_category(tx_desc)
    confidence = 0.85  # Default confidence for successful predictions
    
    print(f"✅ Transaction categorized: '{tx_desc}' -> '{ai_category}'")

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{FIREFFLY_API}/categories", headers=HEADERS)
            if resp.status_code == 302:
                # Authentication failed - token expired/invalid
                print(f"⚠️  Firefly III authentication failed (302 redirect). Token may be expired.")
                return {
                    "status": "AI category predicted (auth required)", 
                    "category": ai_category, 
                    "confidence": confidence,
                    "message": "Category predicted but Firefly III requires re-authentication. Please check/update the API token."
                }
            elif resp.status_code != 200:
                print(f"⚠️  Firefly III API error {resp.status_code}. Category '{ai_category}' predicted but not applied.")
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
    data = await request.json()
    tx_desc = data["transactions"][0]["description"]
    user_cat = data["transactions"][0]["category_name"]

    save_feedback(tx_desc, user_cat)
    retrain_model()  # optional: retrain immediately

    return {"status": "Feedback stored", "category": user_cat}


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
                    <div class="stat-card">
                        <h3>${(summary.average_metrics.accuracy * 100).toFixed(1)}%</h3>
                        <p>Accuracy</p>
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


@app.get("/api/metrics")
async def get_metrics_data():
    """API endpoint to get metrics data in JSON format."""
    try:
        summary = get_model_performance_summary()
        predictions = get_predictions_data()
        
        return {
            "summary": summary,
            "predictions": predictions,
            "storage_type": summary.get("storage_type", "unknown")
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to load metrics: {str(e)}"}
        )