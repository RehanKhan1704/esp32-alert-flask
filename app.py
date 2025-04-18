from flask import Flask, request, jsonify
from twilio.rest import Client
import os
from datetime import datetime

app = Flask(__name__)

# Get Twilio credentials and phone numbers from environment variables
TWILIO_SID = os.environ.get("TWILIO_SID")
TWILIO_AUTH = os.environ.get("TWILIO_AUTH")
TWILIO_PHONE = os.environ.get("TWILIO_PHONE")
TARGET_PHONE = os.environ.get("TARGET_PHONE")
SECONDARY_PHONE = os.environ.get("SECONDARY_PHONE")

# Initialize Twilio client
client = Client(TWILIO_SID, TWILIO_AUTH)

# Global variable to hold last alert timestamp, alert type, and previous records
last_alert_timestamp = None
last_alert_type = None
alert_history = []

@app.route('/alert', methods=['POST'])
def alert():
    global last_alert_timestamp, last_alert_type, alert_history  # Use global variables to store timestamp, alert type, and alert history

    data = request.get_json()
    if not data or "alert" not in data:
        return jsonify({"error": "Invalid input, 'alert' field is required"}), 400

    alert_type = data.get("alert", "").strip().lower()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    last_alert_timestamp = now  # Update the timestamp on each alert
    last_alert_type = alert_type  # Update the alert type

    # Store the alert in the history (keeping the last 5 alerts)
    alert_history.append({"alert": alert_type, "timestamp": now})
    if len(alert_history) > 5:  # Limit the history to the last 5 records
        alert_history.pop(0)

    response = {
        "timestamp": now,
        "alert": alert_type
    }

    try:
        # Decide which voice message to play
        voice_type = "leak" if "leak" in alert_type else "booking"
        voice_url = request.url_root + f"voice.xml?type={voice_type}"

        # Gas Booking Alert: Call TARGET_PHONE and SMS to SECONDARY_PHONE
        if "booking" in alert_type:
            # Call TARGET_PHONE for gas booking
            call = client.calls.create(
                url=voice_url,
                to=TARGET_PHONE,
                from_=TWILIO_PHONE
            )
            response["call_sid"] = call.sid
            response["call_status"] = "initiated"
            response["call_timestamp"] = now  # Include timestamp for gas booking

            # Send SMS to SECONDARY_PHONE only
            sms = client.messages.create(
                body=f"🚨 Alert ({now}): {alert_type.title()}",
                from_=TWILIO_PHONE,
                to=SECONDARY_PHONE
            )
            response["sms_sid"] = sms.sid
            response["sms_status"] = "sent"
            response["sms_timestamp"] = now  # Include timestamp for SMS

            # Include alert type in response
            response["alert_type"] = "Gas Booking Alert"
            response["alert_timestamp"] = now

        # Gas Leakage Alert: Call SECONDARY_PHONE only (No SMS to SECONDARY_PHONE)
        elif "leak" in alert_type:
            # Call SECONDARY_PHONE for gas leakage alert
            gas_call = client.calls.create(
                url=voice_url,
                to=SECONDARY_PHONE,
                from_=TWILIO_PHONE
            )
            response["gas_call_sid"] = gas_call.sid
            response["gas_call_status"] = "initiated"
            response["gas_call_timestamp"] = now  # Include timestamp for gas leakage

            # Include alert type in response
            response["alert_type"] = "Gas Leakage Alert"
            response["alert_timestamp"] = now

        else:
            response["error"] = "Invalid alert type. Valid types are 'booking' or 'leak'."
            return jsonify(response), 400

    except Exception as e:
        response["call_status"] = "failed"
        response["call_error"] = str(e)

    return jsonify(response)

@app.route('/voice.xml', methods=['GET'])
def voice():
    voice_type = request.args.get("type", "default")
    if voice_type == "leak":
        message = "Gas leakage has been detected. Please take immediate action."
    elif voice_type == "booking":
        message = "Your gas cylinder has been successfully booked."
    else:
        message = "Unknown alert."

    response_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="hi-IN" voice="Polly.Aditi">{message}</Say>
</Response>"""

    return response_xml, 200, {'Content-Type': 'application/xml'}

@app.route('/')
def home():
    global last_alert_timestamp, last_alert_type, alert_history

    if last_alert_timestamp:
        timestamp_message = f"Last alert triggered at: {last_alert_timestamp} ({last_alert_type.title()})"
    else:
        timestamp_message = "No alert has been triggered yet."

    # Display the last 5 alert records on the webpage
    alert_records = ""
    for alert in alert_history:
        alert_records += f"<p><strong>{alert['alert'].title()}</strong> at {alert['timestamp']}</p>"

    return f"""
    <h3 style='color:green;'>ESP32 Alert Flask Server Running ✅</h3>
    <p>{timestamp_message}</p>
    <h4>Recent Alerts:</h4>
    {alert_records}
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
