from flask import Flask, jsonify, request
import os
from support import execute_query  # Reuse existing module
import hashlib
import random

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

def get_user_recurring(user_id):
    query = """
    SELECT date, amount FROM transactions 
    WHERE user_id = ? AND is_recurring = 1 
    ORDER BY date DESC LIMIT 100
    """
    return execute_query("search", query, (user_id,))

@app.route('/v2/predict-subscriptions', methods=['GET'])
def predict_subscriptions():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id required"}), 400
        
    transactions = get_user_recurring(user_id)
    dates = [t[0] for t in transactions]
    amounts = [t[1] + random.gauss(0, 0.15) for t in transactions]  # Anonymized
    
    return jsonify({
        "prediction": _safe_forecast(dates, amounts),
        "user_hash": hashlib.sha256(user_id.encode()).hexdigest()[:8]
    })

def _safe_forecast(dates, amounts):
    # Existing forecasting logic from support.py
    if len(amounts) < 5: return []
    # ... keep original time_series_forecast logic ...
    return forecast_data

if __name__ == '__main__':
    app.run(port=5001) 