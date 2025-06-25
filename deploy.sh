#!/bin/bash
# Quick deployment script wrapper

echo "🚀 Quick Deploy - vdw-surfgen"
echo "==============================="

# Install deployment dependencies
echo "📦 Installing deployment dependencies..."
pip install -r deploy_requirements.txt > /dev/null 2>&1

# Run the deployment
python auto_deploy.py "$@"
