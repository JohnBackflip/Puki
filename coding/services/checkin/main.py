from flask import Flask
from flask_cors import CORS
from checkin.routes import checkin_bp

app = Flask(__name__)
CORS(app)
app.json.sort_keys = False

app.register_blueprint(checkin_bp)

@app.route("/")
def root():
    return {"message": "Check-In Microservice"}

@app.route("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=True)
