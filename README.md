# 📊 Stock Analyzer Pro - Web GUI

A professional, modern, and animated web-based GUI for stock analysis of Indian NSE/BSE stocks.

![Stock Analyzer Pro](https://img.shields.io/badge/Version-2.0-blue)
![Python](https://img.shields.io/badge/Python-3.7+-green)
![Flask](https://img.shields.io/badge/Flask-2.0+-purple)

---

## ✨ Features

### 🎯 Smart Analysis
- **Technical Analysis** - RSI, MACD, Bollinger Bands, Stochastic, ADX, ATR
- **Fundamental Analysis** - PE, PB, ROE, Debt/Equity, Profit Margins
- **Historical Analysis** - 52-week range, Support/Resistance levels, Returns
- **Trading Plan** - Buy zones, Sell zones, Targets, Stop Loss

### 🎨 Modern UI/UX
- Dark theme with animated backgrounds
- Smooth transitions and hover effects
- Responsive design (works on mobile)
- Clean, separated sections for each analysis type

### 📱 Action Buttons
- **Buy Analysis** - When and where to buy
- **Sell Analysis** - When to sell if holding
- **Hold Analysis** - Should you hold? For how long?
- **Current Position** - Overall market position summary

---

## 🚀 Quick Start
python -m venv venv 
venv\Scripts\activate
### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the Server
```bash
python run.py
```

### Step 3: Open in Browser
The browser will open automatically at:
```
http://127.0.0.1:8080
```

---

## 📁 Project Structure

```
stock_analyzer/
├── run.py                    ← RUN THIS TO START
├── app.py                    ← Flask API server
├── templates/
│   └── index.html            ← Web GUI (HTML/CSS/JS)
├── stock_loader.py           ← Stock search & loading
├── data_fetcher.py           ← Yahoo Finance data
├── signal_engine.py          ← Signal generation
├── comprehensive_analyzer.py ← Full analysis
├── backtester.py             ← Historical backtesting
├── excel_exporter.py         ← Excel export
├── report_exporter.py        ← Report export
├── requirements.txt          ← Dependencies
└── Indian_Stocks_*.xlsx      ← Stock database
```

---

## 🎯 How to Use

### 1. Search for a Stock
- Type stock symbol (e.g., `RELIANCE`) or company name
- Select from search results
- Click on any result to analyze

### 2. View the Analysis
After selecting a stock:
- **Signal Banner** - Shows BUY/SELL/HOLD with confidence score
- **Score Cards** - Technical, Fundamental, Historical scores
- **Tab Panels** - Detailed data for each analysis type

### 3. Use Action Buttons
- 🟢 **Buy Analysis** - See when to buy
- 🔴 **Sell Analysis** - See when to sell
- 🟡 **Hold Analysis** - See if you should hold
- 📍 **Current Position** - Get summary recommendation

### 4. External Links
- Click "Detailed Technical" for TradingView chart
- Click "Historical Data" for Google Finance
- Click "Latest News" for news search

---

## 🔧 API Endpoints

The Flask server exposes these endpoints:

| Endpoint | Description |
|----------|-------------|
| `GET /api/stats` | Database statistics |
| `GET /api/search?q=QUERY` | Search stocks |
| `GET /api/analyze/SYMBOL` | Full analysis |
| `GET /api/quick-signal/SYMBOL` | Quick signal only |
| `GET /api/backtest/SYMBOL?date=YYYY-MM-DD` | Backtest |
| `GET /api/current-price/SYMBOL` | Current price |
| `GET /api/stock-info/SYMBOL` | Stock info |

---

## 📊 Sample Analysis Output

When you analyze a stock like RELIANCE, you get:

### Signal Banner
```
🟢 BUY
Strong Signal - High Confidence
Overall Score: 72
```

### Technical Indicators
- RSI: 45.2 (Neutral)
- MACD Histogram: 2.35 (Bullish)
- SMA 20/50/200: Above all
- ADX: 28.5 (Trending)

### Trading Plan
- Entry: ₹2,450.50
- Target 1: ₹2,550.00 (+4.1%)
- Target 2: ₹2,620.00 (+6.9%)
- Stop Loss: ₹2,380.00 (-2.9%)
- Risk:Reward: 1:2.5

---

## ⚠️ Important Notes

1. **Backend Logic Unchanged**
   - All backend Python files are exactly as they were
   - Only a Flask wrapper (`app.py`) and frontend (`index.html`) added
   - No logic modifications

2. **Internet Required**
   - Stock data is fetched from Yahoo Finance
   - Ensure internet connection for analysis

3. **Educational Purpose**
   - Signals are for educational purposes only
   - Always do your own research before trading

---

## 🛠️ Troubleshooting

### "Module not found" error
```bash
pip install -r requirements.txt
```

### Port 5000 already in use
Edit `run.py` and change port number:
```python
app.run(port=5001)  # Change to 5001 or any free port
```

### Excel file not found
Ensure `Indian_Stocks_Complete_Market_Cap_Classification.xlsx` is in the same folder.

### Slow first load
First analysis takes longer as it downloads stock data. Subsequent analyses are faster due to caching.

---

## 🎨 UI Customization

The UI uses CSS variables for easy customization. Edit `templates/index.html`:

```css
:root {
    --accent-green: #00d68f;   /* Buy signals */
    --accent-red: #ff4757;     /* Sell signals */
    --accent-yellow: #ffd43b;  /* Hold signals */
    --accent-purple: #a855f7;  /* Accent color */
}
```

---

## 📧 Support

For issues with the analysis logic, check the original backend files.
For UI issues, check the `templates/index.html` file.

---

**Happy Trading! 📈**

*Disclaimer: This tool is for educational purposes only. Trading involves risk. Always do your own research.*
