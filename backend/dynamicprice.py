from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from os import environ
import json
import pika
import invokes 

app = Flask(__name__)
CORS(app)

# Get URLs from environment variables - use Docker service names instead of localhost
PRICE_URL = environ.get('PRICE_URL', 'http://price:5003')
PROMOTION_URL = environ.get('PROMOTION_URL', 'http://promotion:5004')

# health check
@app.route("/health")
def health():
    return {"status": "healthy"}

# Get dynamic price
@app.route("/dynamicprice", methods=["GET"])
def get_dynamic_price():
    room_type = request.args.get("room_type")
    date = request.args.get("date")

    if not room_type or not date:
        return jsonify({"code": 400, "message": "Missing room_type or date parameter"}), 400

    try:
        # Step 1: Get base price from price service
        price_url = f"{PRICE_URL}/price/{room_type}"
        print(f"Fetching price from: {price_url}")
        price_response = invokes.invoke_http(price_url, method="GET")
        print(f"Price service response: {price_response}")
        
        if not isinstance(price_response, list) and price_response.get("code") != 200:
            return jsonify({"code": 404, "message": f"No base price found for room_type '{room_type}'"}), 404

        # Handle both list format and dict with data field format
        if isinstance(price_response, list):
            prices = price_response
        else:
            prices = price_response.get("data", [])
            
        if not prices:
            return jsonify({"code": 404, "message": f"No prices found for room_type '{room_type}'"}), 404

        base_price = prices[0]["price"]  # Use first price returned

        # Step 2: Get applicable promotions from promotion service
        promo_url = f"{PROMOTION_URL}/promotion/applicable?room_type={room_type}&date={date}"
        print(f"Fetching promotions from: {promo_url}")
        promo_response = invokes.invoke_http(promo_url, method="GET")
        print(f"Promotion service response: {promo_response}")
        
        discount = 0
        promo_data = None

        if promo_response.get("code") == 200:
            promo_payload = promo_response.get("data", {})
            discount = promo_payload.get("discount", 0)
            promo_data = promo_payload

        # Step 3: Compute final price
        final_price = round(base_price * (1 - discount / 100), 2)

        return jsonify({
            "code": 200,
            "data": {
                "base_price": base_price,
                "discount_applied": discount,
                "final_price": final_price,
                "room_type": room_type,
                "date": date,
                "promotion": promo_data
            }
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"code": 500, "message": f"Unexpected error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5016, debug=True)
