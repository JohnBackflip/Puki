from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import invokes
from os import environ
import traceback

app = Flask(__name__)
CORS(app)

# Service URLs - use Docker service names instead of localhost
BOOKING_URL = environ.get('BOOKING_URL', 'http://booking:5002')
GUEST_URL = environ.get('GUEST_URL', 'http://guest:5011')
ROOM_URL = environ.get('ROOM_URL', 'http://room:5008')
DYNAMICPRICE_URL = environ.get('DYNAMICPRICE_URL', 'http://dynamicprice:5016')

# Health check
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200

# Make a booking (without room assignment)
@app.route("/makebooking", methods=["POST"])
def create_booking():
    try:
        data = request.get_json()
        print("Received data:", data)

        if not data:
            return jsonify({"code": 400, "message": "No data received"}), 400

        required_fields = ["guest_id", "room_type", "check_in", "check_out", "price"]
        if not all(field in data for field in required_fields):
            return jsonify({"code": 400, "message": "Missing required fields."}), 400

        # Validate and parse dates
        room_type = data["room_type"]
        check_in_str = data["check_in"]
        check_out_str = data["check_out"]
        try:
            check_in = datetime.strptime(check_in_str, "%Y-%m-%d").date()
            check_out = datetime.strptime(check_out_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"code": 400, "message": "Invalid date format. Use YYYY-MM-DD."}), 400

        if check_out <= check_in:
            return jsonify({"code": 400, "message": "Check-out date must be later than check-in date."}), 400

        # Check guest
        guest_url = f"{GUEST_URL}/guest/{data['guest_id']}"
        guest_response = invokes.invoke_http(guest_url, method="GET")
        print("Guest response:", guest_response)

        if not isinstance(guest_response, dict) or guest_response.get("code") != 200:
            return jsonify({"code": 400, "message": "Invalid guest_id. Guest does not exist."}), 400

        # Fetch dynamic price
        price_url = f"{DYNAMICPRICE_URL}/dynamicprice?room_type={room_type}&date={check_in}"
        print(f"Calling dynamic price URL: {price_url}")
        dynamic_price_response = invokes.invoke_http(price_url, method="GET")
        print("Dynamic price response:", dynamic_price_response)

        if not isinstance(dynamic_price_response, dict):
            return jsonify({"code": 500, "message": f"Invalid response from dynamic price service: {dynamic_price_response}"}), 500

        if dynamic_price_response.get("code") != 200:
            return jsonify({"code": 500, "message": "Failed to get dynamic price", "details": dynamic_price_response}), 500

        price_data = dynamic_price_response.get("data", {})
        final_price = price_data.get("final_price")

        if final_price is None:
            return jsonify({"code": 500, "message": "Dynamic price missing from response"}), 500

        print(f"Final dynamic price: {final_price}")

        # Create booking payload
        booking_payload = {
            "guest_id": data["guest_id"],
            "room_type": room_type,
            "check_in": check_in_str,
            "check_out": check_out_str,
            "price": final_price
        }

        print("Booking payload:", booking_payload)

        booking_response = invokes.invoke_http(f"{BOOKING_URL}/booking", method="POST", json=booking_payload)
        print("Booking response:", booking_response)

        if not isinstance(booking_response, dict):
            return jsonify({"code": 500, "message": "Invalid response from booking service"}), 500

        if booking_response.get("code") != 201:
            return jsonify({"code": 500, "message": f"Booking creation failed: {booking_response.get('message')}"}), 500

        return jsonify({"code": 201, "data": booking_response["data"]}), 201

    except Exception as e:
        traceback.print_exc()
        return jsonify({"code": 500, "message": f"Internal server error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5013, debug=True)
