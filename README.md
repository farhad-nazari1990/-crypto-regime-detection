# README.md

# 📊 AI-Driven Bitcoin Market Regime Intelligence

Institutional-grade Bitcoin market regime detection demo built with Streamlit.

This application demonstrates how Hidden Markov Models (HMMs), structural break analysis, and dynamic allocation frameworks can be combined into an interactive institutional analytics dashboard.

Designed for:
- Quant funds
- Crypto hedge funds
- Proprietary trading firms
- Digital asset allocators
- Institutional founders
- Research teams

---

# 🚀 Features

## ✅ Executive Dashboard
- Institutional hero section
- Market intelligence positioning
- KPI summary metrics

## ✅ Interactive Regime Visualization
- BTC price chart
- Regime overlays
- Structural break markers
- Zoomable Plotly interface

## ✅ Probability Heatmap
- Time-based regime probability visualization
- Automatic detection of probability columns

## ✅ Regime Duration Analytics
- Average duration
- Max duration
- Regime occurrence counts

## ✅ Performance Analytics
- Sharpe ratio comparison
- Volatility metrics
- Drawdown statistics
- Win rate analysis

## ✅ Strategy Backtesting
- Best-regime-only exposure strategy
- Buy & Hold comparison

## ✅ Dynamic Allocation Simulation
- Interactive sidebar controls
- Custom regime allocations
- Real-time equity curve recomputation

## ✅ PDF Executive Reporting
- In-memory PDF generation
- Institutional-ready downloadable report

---

# 📁 Project Structure
```text
crypto-regime-demo/
│
├── app.py
├── requirements.txt
├── README.md
│
└── data/
├── btc_clean.csv
├── hmm_labels.csv
├── cpd_points.csv
└── performance_per_regime.csv

---

# 📂 Required Data Files

## 1️⃣ btc_clean.csv

Expected columns:

text
date
open
high
low
close
volume

Alternative naming conventions are handled safely.

---

## 2️⃣ hmm_labels.csv

Expected columns:

text
date
state

Optional probability columns:

text
prob_0
prob_1
prob_2
...

---

## 3️⃣ cpd_points.csv

Expected columns:

text
index

---

## 4️⃣ performance_per_regime.csv

Expected columns:

text
regime
mean_return
volatility
sharpe_ratio
max_drawdown
win_rate

---

# ▶️ Local Run

## 1. Install dependencies

bash
pip install -r requirements.txt

## 2. Run the Streamlit app

bash
streamlit run app.py

---

# ☁️ Deploy to Streamlit Cloud

## Step 1
Push the repository to GitHub.

## Step 2
Open:

text
https://share.streamlit.io

## Step 3
Connect your GitHub repository.

## Step 4
Set:

text
Main file path: app.py

## Step 5
Deploy.

---

# 🧠 Technical Notes

- Fully compatible with Streamlit Cloud
- No OS-specific dependencies
- Pure pip-installable stack
- Defensive schema handling
- Graceful failure behavior
- Cached data loading
- Modular architecture

---

# 📸 Screenshot Placeholder

Add screenshots here after deployment.

Example:

markdown
![Dashboard Screenshot](screenshots/dashboard.png)

---

# 📦 Requirements

text
streamlit
pandas
numpy
plotly
reportlab

---

# 📜 License

Internal demo / commercial presentation use.
