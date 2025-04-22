#include <WiFi.h>
#include <HTTPClient.h>
#include <HX711_ADC.h>

// Wi-Fi Credentials
const char* ssid = "oplus_co_aphwaw";
const char* password = "11223344";

// Flask server endpoint
const char* serverURL = "https://esp32-alert-flask-production.up.railway.app/alert";

// Pins for HX711
const int HX711_dout = 4;
const int HX711_sck = 5;

// Gas sensor analog pin
const int gasSensorPin = 34;

// Buzzer pin
const int buzzerPin = 14;

// HX711 Object
HX711_ADC LoadCell(HX711_dout, HX711_sck);

// Thresholds
const float weightThresholdKg = 2.0;
const int gasThreshold = 1000;

// Alert flags
bool weight_alert_sent = false;
bool gas_alert_sent = false;

// Function to send alert
void sendAlert(String message) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverURL);
    http.setTimeout(10000);  // 10 seconds timeout
    http.addHeader("Content-Type", "application/json");

    String jsonPayload = "{\"alert\":\"" + message + "\"}";

    Serial.print("Sending alert: ");
    Serial.println(jsonPayload);

    int httpResponseCode = http.POST(jsonPayload);

    if (httpResponseCode > 0) {
      Serial.print("HTTP Response Code: ");
      Serial.println(httpResponseCode);

      String responseBody = http.getString();
      Serial.print("Server Response: ");
      Serial.println(responseBody);
    } else {
      Serial.println("⚠️ Failed to send HTTP POST request!");
      Serial.print("Error: ");
      Serial.println(http.errorToString(httpResponseCode));
    }

    http.end();
  } else {
    Serial.println("❌ Wi-Fi not connected! Skipping alert.");
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  pinMode(buzzerPin, OUTPUT);
  digitalWrite(buzzerPin, LOW);

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ Connected to WiFi!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  LoadCell.begin();
  LoadCell.start(2000);
  LoadCell.setCalFactor(210.0); // <- Adjust after calibration
  LoadCell.setTareOffset(LoadCell.getTareOffset()); // Optional

  Serial.println("Load cell initialized.");
}

void loop() {
  LoadCell.update();
  float weight = LoadCell.getData();
  int gasValue = analogRead(gasSensorPin);

  Serial.print("Weight: ");
  Serial.print(weight, 2);
  Serial.print(" kg, Gas: ");
  Serial.println(gasValue);

  // --- Weight Alert Logic ---
  if (weight <= weightThresholdKg && !weight_alert_sent) {
    sendAlert("{Booking}.. Gas has been booked");
    weight_alert_sent = true;
  } else if (weight > weightThresholdKg + 0.5) {
    weight_alert_sent = false;
  }

  // --- Gas Alert Logic ---
  if (gasValue > gasThreshold) {
    digitalWrite(buzzerPin, HIGH);
    if (!gas_alert_sent) {
      sendAlert("Gas leakage has been detected");
      gas_alert_sent = true;
    }
  } else {
    digitalWrite(buzzerPin, LOW);
    gas_alert_sent = false;
  }

  delay(3000); // 3 seconds delay between reads
}
