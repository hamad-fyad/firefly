"""
UI Routes Module
Handles serving HTML templates for analytics dashboards
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Get the directory where this file is located
CURRENT_DIR = Path(__file__).parent
TEMPLATES_DIR = CURRENT_DIR / "templates"

def add_ui_routes(app: FastAPI):
    """Add all UI routes that serve HTML templates."""
    
    def read_template(template_name: str) -> str:
        """Read HTML template file and return content."""
        template_path = TEMPLATES_DIR / template_name
        try:
            with open(template_path, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            logger.error(f"Template not found: {template_path}")
            return f"<html><body><h1>Template not found: {template_name}</h1></body></html>"
        except Exception as e:
            logger.error(f"Error reading template {template_name}: {str(e)}")
            return f"<html><body><h1>Error loading template: {str(e)}</h1></body></html>"
    
    @app.get("/analytics-hub", response_class=HTMLResponse)
    async def analytics_hub_ui():
        """Serve the main Analytics Hub dashboard."""
        return HTMLResponse(content=read_template("analytics_hub.html"))
    
    @app.get("/transaction-analyzer", response_class=HTMLResponse)
    async def transaction_analyzer_ui():
        """Serve the AI Transaction Analyzer dashboard."""
        return HTMLResponse(content=read_template("transaction_analyzer.html"))
    
    # @app.get("/budget-analyzer", response_class=HTMLResponse)
    # async def budget_analyzer_ui():
    #     """Serve the AI Budget Analyzer dashboard."""
    #     return HTMLResponse(content=read_template("budget_analyzer.html"))
    
    @app.get("/metrics", response_class=HTMLResponse)
    async def metrics_dashboard_ui():
        """Serve the AI Metrics Dashboard."""
        return HTMLResponse(content=read_template("metrics_dashboard.html"))
    
    logger.info("✅ UI routes loaded successfully")
    logger.info("🎯 Available UI endpoints:")
    logger.info("   • /analytics-hub - Main AI Analytics Dashboard")
    logger.info("   • /transaction-analyzer - AI Transaction Analysis")
    # logger.info("   • /budget-analyzer - AI Budget Analysis")
    logger.info("   • /metrics - AI Performance Metrics Dashboard")