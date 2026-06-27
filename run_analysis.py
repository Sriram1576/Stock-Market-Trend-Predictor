
# run_analysis.py - Simple usage example
from twelve_data_backend import StockPredictor
import json
import os
from dotenv import load_dotenv

load_dotenv()

def analyze_stocks():
    # Initialize with your API key
    API_KEY = os.getenv('TWELVE_DATA_API_KEY', 'YOUR_API_KEY_HERE')
    predictor = StockPredictor(API_KEY)

    # Analyze popular stocks
    stocks_to_analyze = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']

    results = {}
    for symbol in stocks_to_analyze:
        print(f"\n🔍 Analyzing {symbol}...")
        result = predictor.analyze_stock(symbol, 'random_forest')

        if 'error' not in result:
            results[symbol] = result
            quote = result['quote']
            prediction = result['prediction']

            print(f"✅ {symbol}: ${quote['price']:.2f} ({quote['change']:+.2f})")
            print(f"   Prediction: {prediction['direction']} ({prediction['confidence']:.1f}%)")
        else:
            print(f"❌ Error analyzing {symbol}: {result['error']}")

    # Save results
    with open('analysis_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n📊 Analysis complete! Results saved to analysis_results.json")
    return results

if __name__ == "__main__":
    analyze_stocks()
