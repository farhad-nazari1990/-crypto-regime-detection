# setup.ps1

Write-Host "🚀 Setting up Bitcoin Regime Intelligence Demo..." -ForegroundColor Green

# Create data directory
New-Item -ItemType Directory -Force -Path data | Out-Null

# Install dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Generate sample data
Write-Host "📊 Generating sample data..." -ForegroundColor Yellow
python generate_sample_data.py

Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To run the app:" -ForegroundColor Cyan
Write-Host "  streamlit run app.py" -ForegroundColor White
Write-Host ""
