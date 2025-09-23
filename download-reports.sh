#!/bin/bash

# Download and organize all test reports from latest GitHub Actions run
# Usage: ./download-reports.sh [RUN_ID]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Repository info
REPO="hamad-fyad/firefly"
RUN_ID=${1:-$(gh run list --repo $REPO --limit 1 --json databaseId --jq '.[0].databaseId')}

echo -e "${BLUE}📥 Downloading test reports from GitHub Actions run #${RUN_ID}${NC}"

# Create reports directory
REPORTS_DIR="local-reports/run-${RUN_ID}"
mkdir -p "$REPORTS_DIR"
cd "$REPORTS_DIR"

echo -e "${YELLOW}📁 Created directory: $(pwd)${NC}"

# Download artifacts
echo -e "${BLUE}🔽 Downloading artifacts...${NC}"

# Function to download artifact safely
download_artifact() {
    local artifact_name=$1
    local display_name=$2
    
    echo -e "${YELLOW}  Downloading ${display_name}...${NC}"
    if gh run download $RUN_ID --repo $REPO --name "$artifact_name" --dir "$artifact_name" 2>/dev/null; then
        echo -e "${GREEN}  ✅ ${display_name} downloaded${NC}"
    else
        echo -e "${RED}  ❌ ${display_name} not found or failed to download${NC}"
    fi
}

# Download all report types
download_artifact "allure-report-firefly-${RUN_ID}" "Allure Test Report"
download_artifact "security-reports-${RUN_ID}" "Security Reports"
download_artifact "code-quality-report-${RUN_ID}" "Code Quality Reports"
download_artifact "load-test-reports-${RUN_ID}" "Load Test Reports"
download_artifact "dependency-reports-${RUN_ID}" "Dependency Reports"

# Create a local index file
echo -e "${BLUE}📄 Creating local index file...${NC}"
cat > index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Firefly III Test Reports - Local View</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #f8f9fa; }
        .container { max-width: 1000px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; text-align: center; margin-bottom: 30px; }
        .report-section { margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; }
        .file-list { list-style: none; padding: 0; }
        .file-list li { margin: 5px 0; }
        .file-link { color: #3498db; text-decoration: none; }
        .file-link:hover { text-decoration: underline; }
        .section-title { color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 Firefly III Test Reports (Local)</h1>
        <p><strong>Run ID:</strong> RUN_ID_PLACEHOLDER</p>
        <p><strong>Downloaded:</strong> TIMESTAMP_PLACEHOLDER</p>
        
        <div class="report-section">
            <h2 class="section-title">📊 Available Reports</h2>
            <ul class="file-list">
                <li>📁 <strong>allure-report-firefly-RUN_ID_PLACEHOLDER/</strong> - Main Allure test report</li>
                <li>📁 <strong>security-reports-RUN_ID_PLACEHOLDER/</strong> - Security analysis (Bandit, Safety, Semgrep)</li>
                <li>📁 <strong>code-quality-report-RUN_ID_PLACEHOLDER/</strong> - Code quality analysis</li>
                <li>📁 <strong>load-test-reports-RUN_ID_PLACEHOLDER/</strong> - Load testing results</li>
                <li>📁 <strong>dependency-reports-RUN_ID_PLACEHOLDER/</strong> - Dependency analysis</li>
            </ul>
        </div>
        
        <div class="report-section">
            <h2 class="section-title">🚀 Quick Access</h2>
            <p>Open the <code>index.html</code> file inside each directory to view the reports, or check the markdown summaries:</p>
            <ul class="file-list">
                <li><a href="security-reports-RUN_ID_PLACEHOLDER/security-summary.md" class="file-link">Security Summary</a></li>
                <li><a href="code-quality-report-RUN_ID_PLACEHOLDER/quality-summary.md" class="file-link">Quality Summary</a></li>
                <li><a href="load-test-reports-RUN_ID_PLACEHOLDER/load-summary.md" class="file-link">Load Test Summary</a></li>
                <li><a href="dependency-reports-RUN_ID_PLACEHOLDER/dependency-summary.md" class="file-link">Dependency Summary</a></li>
            </ul>
        </div>
    </div>
</body>
</html>
EOF

# Replace placeholders
sed -i '' "s/RUN_ID_PLACEHOLDER/${RUN_ID}/g" index.html
sed -i '' "s/TIMESTAMP_PLACEHOLDER/$(date)/" index.html

echo -e "${GREEN}✅ All reports downloaded successfully!${NC}"
echo -e "${BLUE}📁 Reports location: $(pwd)${NC}"
echo -e "${YELLOW}🌐 Open index.html in your browser to view all reports${NC}"

# Optional: Open in browser (macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${BLUE}🚀 Opening in browser...${NC}"
    open index.html
fi