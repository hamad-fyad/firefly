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
FIREFFLY_TOKEN = os.environ.get("FIREFLY_TOKEN", "your_firefly_token")
HEADERS = {"Authorization": f"Bearer {FIREFFLY_TOKEN}"}


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker."""
    try:
        # Check if OpenAI client can be initialized
        from app.ai_model import get_openai_client
        client = get_openai_client()
        model_status = "available" if client else "openai_key_missing"
        
        return {
            "status": "healthy",
            "model_status": model_status,
            "model_type": "openai"
        }
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


@app.get("/debug")
async def debug_info():
    """Debug endpoint to check OpenAI status and environment."""
    import os
    from app.ai_model import get_openai_client, fallback_categorization
    
    try:
        # Check OpenAI configuration
        api_key = os.environ.get("OPENAI_API_KEY")
        client = get_openai_client()
        
        # Test fallback
        fallback_test = fallback_categorization("grocery store purchase")
        
        debug_info = {
            "openai_api_key_configured": bool(api_key),
            "openai_api_key_length": len(api_key) if api_key else 0,
            "openai_client_available": client is not None,
            "fallback_test": {
                "input": "grocery store purchase",
                "output": fallback_test
            },
            "environment_vars": {
                "OPENAI_API_KEY": "***" if api_key else "NOT_SET",
                "FIREFLY_TOKEN": "***" if os.environ.get("FIREFLY_TOKEN") else "NOT_SET"
            }
        }
        
        # Test OpenAI if available
        if client:
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Say 'test'"}],
                    max_tokens=5,
                    timeout=5
                )
                debug_info["openai_test"] = "SUCCESS"
                debug_info["openai_response"] = response.choices[0].message.content
            except Exception as e:
                debug_info["openai_test"] = "FAILED"
                debug_info["openai_error"] = str(e)
        else:
            debug_info["openai_test"] = "SKIPPED - No client"
            
        return debug_info
        
    except Exception as e:
        return {"error": str(e), "debug_failed": True}


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
