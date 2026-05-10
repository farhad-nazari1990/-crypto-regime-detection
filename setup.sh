#!/bin/bash
# setup.sh

echo "🚀 Setting up Bitcoin Regime Intelligence Demo..."

# Create data directory
mkdir -p data

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Generate sample data
echo "📊 Generating sample data..."
python generate_sample_data.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run the app:"
echo "  streamlit run app.py"
echo ""
