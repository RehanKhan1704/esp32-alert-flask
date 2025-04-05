from flask import Flask, request, jsonify
from twilio.rest import Client
import os

app = Flask(__name__)

TWILIO_SID = os.environ.get("TWILIO_SID")
TWILIO_AUTH = os.environ.get("TWILIO_AUTH")
TWILIO_PHONE = os.environ.get("TWILIO_PHONE")
TARGET_PHONE = os.environ.get("TARGET_PHONE")  # like +91xxxxxxxxxx

client = Client(TWILIO_SID, TWILIO_AUTH)

@app.route('/alert', methods=['POST'])
def alert():
    data = request.get_json()
    alert_type = data.get("alert")

    print(f"Received alert: {alert_type}")

    try:
        call = client.calls.create(
            url=request.url_root + "voice.xml",  # dynamically link to hosted XML
            to=TARGET_PHONE,
            from_=TWILIO_PHONE
        )
        return jsonify({"status": "calling", "sid": call.sid})
    except Exception as e:
        print("Call error:", e)
        return jsonify({"status": "failed", "error": str(e)}), 500

@app.route('/voice.xml', methods=['GET'])
def voice():
    return open('voice.xml').read(), 200, {'Content-Type': 'application/xml'}

@app.route('/')
def home():
    return "<h3>ESP32 Alert Flask Server Running</h3>"

if __name__ == '__main__':
    app.run()
