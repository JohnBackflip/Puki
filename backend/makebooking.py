from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import invokes
from os import environ

app = Flask(__name__)
CORS(app)

# Service URLs
BOOKING_URL = environ.get('BOOKING_URL', 'http://localhost:5002')
GUEST_URL = environ.get('GUEST_URL', 'http://localhost:5011')
ROOM_URL = environ.get('ROOM_URL', 'http://localhost:5008')
PRICE_URL = environ.get('PRICE_URL', 'http://localhost:5009')

#health check
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200

#make a booking
@app.route("/makebooking", methods=["POST"])
def create_booking():
    data = request.get_json()

    # Validate dates
    check_in = datetime.strptime(data["check_in"], "%Y-%m-%d").date()
    check_out = datetime.strptime(data["check_out"], "%Y-%m-%d").date()

    if check_out <= check_in:
        return jsonify({"code": 400, "message": "Check-out date must be later than check-in date."}), 400

    # Verify guest exists
    guest_check_url = f"{GUEST_URL}/guest/{data['guest_id']}"
    print("Checking guest at URL:", guest_check_url)  # Debug log
    guest_response = invokes.invoke_http(guest_check_url, method="GET")
    print("Guest response:", guest_response)  # Debug log
    
    # Check if the response has a code field and data
    if not isinstance(guest_response, dict):
        print("Response is not a dict")  # Debug log
        return jsonify({"code": 400, "message": "Invalid guest_id. Guest does not exist."}), 400

    if 'code' not in guest_response:
        print("Response missing code field")  # Debug log
        return jsonify({"code": 400, "message": "Invalid guest_id. Guest does not exist."}), 400

    if 'data' not in guest_response:
        print("Response missing data field")  # Debug log
        return jsonify({"code": 400, "message": "Invalid guest_id. Guest does not exist."}), 400

    if guest_response['code'] != 200:
        print("Response code is not 200:", guest_response['code'])  # Debug log
        return jsonify({"code": 400, "message": "Invalid guest_id. Guest does not exist."}), 400

    if not guest_response['data']:
        print("Response data is empty")  # Debug log
        return jsonify({"code": 400, "message": "Invalid guest_id. Guest does not exist."}), 400

    # Extract guest data
    guest_data = guest_response['data']
    print("Guest data:", guest_data)  # Debug log

    # Check room availability
    availability_check_url = f"{BOOKING_URL}/booking/availability"
    availability_data = {
        "room_id": data["room_id"],
        "check_in": data["check_in"],
        "check_out": data["check_out"]
    }
    availability_response = invokes.invoke_http(availability_check_url, method="POST", json=availability_data)
    print("Availability response:", availability_response)  # Debug log
    
    if not isinstance(availability_response, dict) or not availability_response.get("available", False):
        return jsonify({"code": 400, "message": "Room is already booked for the selected period."}), 400

    # Fetch expected price from PRICE_URL
    price_url = f"{PRICE_URL}/price/{data['room_type']}"
    price_response = invokes.invoke_http(price_url, method="GET")

    if price_response.get("code") != 200:
        return jsonify({"code": 500, "message": "Failed to retrieve price data."}), 500

    expected_price = price_response.get("data", {}).get("price")

    if expected_price is None:
        return jsonify({"code": 500, "message": "Missing price data from price service."}), 500

    # Check if provided price matches expected price
    if float(data["price"]) != float(expected_price):
        return jsonify({
            "code": 400,
            "message": f"Price mismatch. Expected: {expected_price}, Provided: {data['price']}"
        }), 400

    # Create the booking in the booking service
    create_booking_url = f"{BOOKING_URL}/booking"
    booking_response = invokes.invoke_http(create_booking_url, method="POST", json=data)
    print("Booking response:", booking_response)  # Debug log
    
    if not isinstance(booking_response, dict):
        print("Invalid booking response format")  # Debug log
        return jsonify({"code": 500, "message": "Error creating booking: Invalid response format."}), 500
        
    if booking_response.get("code") != 201:
        print("Booking creation failed with code:", booking_response.get("code"))  # Debug log
        return jsonify({"code": 500, "message": f"Error creating booking: {booking_response.get('message', 'Unknown error')}"}), 500

    booking_data = booking_response.get("data")
    if not booking_data:
        return jsonify({"code": 500, "message": "Missing booking data from response."}), 500

    return jsonify({"code": 201, "data": booking_data}), 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5013, debug=True)