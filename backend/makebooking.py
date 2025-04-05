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
PRICE_URL = environ.get('PRICE_URL', 'http://localhost:5003')  # Updated to port 5003
HOUSEKEEPER_URL = environ.get('HOUSEKEEPER_URL', 'http://localhost:5014')  # Added housekeeper URL

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
    print("Price response:", price_response)  # Debug log

    # Handle different response formats from the price service
    if isinstance(price_response, str):
        try:
            import json
            price_response = json.loads(price_response)
            print("Parsed price response:", price_response)
        except Exception as e:
            print("Error parsing price response:", str(e))
            return jsonify({"code": 500, "message": f"Failed to parse price data: {str(e)}"}), 500

    # Handle both list and dictionary responses
    if isinstance(price_response, dict):
        # If it's a dictionary with data field containing a list
        if "data" in price_response and isinstance(price_response["data"], list):
            price_list = price_response["data"]
        # If it's a dictionary with a direct price field
        elif "price" in price_response:
            expected_price = price_response["price"]
            if float(data["price"]) != float(expected_price):
                return jsonify({
                    "code": 400,
                    "message": f"Price mismatch. Expected: {expected_price}, Provided: {data['price']}"
                }), 400
            # Skip the rest of the price checking logic
            print(f"Using direct price from response: {expected_price}")
            goto_create_booking = True
        else:
            return jsonify({"code": 500, "message": "Missing price data in response"}), 500
    elif isinstance(price_response, list):
        price_list = price_response
    else:
        return jsonify({"code": 500, "message": f"Invalid price data format: {type(price_response)}"}), 500

    # Only do this price list processing if we don't have a direct price
    goto_create_booking = locals().get("goto_create_booking", False)
    if not goto_create_booking:
        if not price_list:
            return jsonify({"code": 500, "message": "No price data found for the room type."}), 500

        # Get the price for the selected room_id
        room_id = data["room_id"]
        expected_price = None
        for room in price_list:
            if room.get("room_id") == room_id:
                expected_price = room.get("price")
                break
        
        # If no exact room match, use the first room of the requested type
        if expected_price is None and price_list:
            expected_price = price_list[0].get("price")

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