#!/bin/bash
# Production Server Runner
# This script runs the Streamlit app exactly like it would run in production

echo "🚀 Starting Production Server Test"
echo "=================================="

# Activate virtual environment
source production_test_env/bin/activate

# Set production environment variables
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_SERVER_ENABLE_CORS=false
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
export STREAMLIT_LOGGER_LEVEL=info

echo "✅ Environment variables set"

# Start server with production settings (same as render.yaml)
echo "🖥️  Starting server on http://localhost:8504"
echo "📝 Watch for any errors in the output below"
echo "🛑 Press Ctrl+C to stop the server"
echo ""

streamlit run app.py \
  --server.port=8504 \
  --server.address=0.0.0.0 \
  --server.headless=true \
  --server.enableCORS=false \
  --server.maxUploadSize=100

echo ""
echo "🛑 Server stopped"