# Stock Market Trend Predictor 📈

A comprehensive stock market analysis and prediction tool that leverages real-time data, technical indicators, and machine learning to forecast stock price movements.

## 🚀 Features

- **Real-Time Data**: Integrates with the Twelve Data API to fetch real-time stock quotes and historical time series data.
- **Technical Analysis**: Automatically calculates key technical indicators including EMA (13 & 21), MACD, and RSI.
- **Machine Learning Predictions**: Utilizes Random Forest and Logistic Regression models trained on historical data and technical indicators to predict next-day price direction (UP/DOWN) and provide a confidence score.
- **Feature Importance**: Analyzes and ranks which technical indicators most strongly influence the price predictions.
- **Web Interface**: Includes a responsive frontend (`index.html`, `style.css`, `app.js`) to visually present the predictions and stock data.

## 🛠️ Technology Stack

- **Backend / Data Science**: Python, `pandas`, `pandas-ta`, `scikit-learn`, `numpy`
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **External APIs**: Twelve Data API

## 📋 Prerequisites

To run this project, you need Python installed along with the required libraries. 

Install the required Python packages:
```bash
pip install -r requirements_twelve_data.txt
```

*Note: You will also need a valid Twelve Data API key to fetch real-time stock information.*

## ⚙️ Setup & Usage

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Sriram1576/Stock-Market-Trend-Predictor.git
   cd Stock-Market-Trend-Predictor
   ```

2. **Run the backend script:**
   The `twelve_data_backend.py` file contains the core logic for fetching data and training models.
   You can run the analysis script to see predictions for popular stocks (e.g., AAPL, MSFT, GOOGL, TSLA, NVDA):
   ```bash
   python run_analysis.py
   ```

3. **Web Interface:**
   Simply open `index.html` in your web browser to view the stock analysis dashboard.

## ⚠️ Disclaimer
This tool is for educational and informational purposes only. It is not intended as financial advice. Always do your own research and consult with a qualified financial advisor before making investment decisions.