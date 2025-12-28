#include <Wire.h>
#include <Adafruit_MLX90614.h>
#include <MFRC522.h>
#include <LiquidCrystal_I2C.h>
#include <ArduinoJson.h>

// Pin definitions
#define BUZZER_PIN 15
#define TRIG_PIN 12
#define ECHO_PIN 14
#define SS_PIN 5
#define RST_PIN 4

// Device objects
Adafruit_MLX90614 mlx = Adafruit_MLX90614();
MFRC522 mfrc522(SS_PIN, RST_PIN);
LiquidCrystal_I2C lcd(0x27, 16, 2);

// Variables
unsigned long lastScanTime = 0;
const unsigned long SCAN_DELAY = 3000;
bool objectDetected = false;
float feverThreshold = 37.5;
float tempOffset = 0.0; // Calibration offset

void setup() {
  Serial.begin(115200);
  
  // Initialize hardware
  initializePins();
  initializeI2C();
  initializeRFID();
  initializeLCD();
  
  Serial.println("AttemptDance System Ready");
  Serial.println("JSON:{\"status\":\"ready\",\"threshold\":37.5}");
  
  playWelcomeTone();
  showWelcomeScreen();
}

void initializePins() {
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  digitalWrite(BUZZER_PIN, LOW); // Ensure buzzer is off initially
}

void initializeI2C() {
  Wire.begin();
  
  // Initialize MLX90614 with retry
  int attempts = 0;
  while (!mlx.begin() && attempts < 3) {
    Serial.println("MLX90614 init failed, retrying...");
    delay(1000);
    attempts++;
  }
  
  if (attempts == 3) {
    Serial.println("ERROR: MLX90614 not found!");
    lcdPrint("Temp Sensor", "NOT FOUND!");
    while(1);
  }
}

void initializeRFID() {
  SPI.begin();
  mfrc522.PCD_Init();
  delay(100);
  
  // Check RFID module
  byte v = mfrc522.PCD_ReadRegister(mfrc522.VersionReg);
  if (v == 0x00 || v == 0xFF) {
    Serial.println("ERROR: RFID module not found!");
    lcdPrint("RFID Module", "NOT FOUND!");
  } else {
    Serial.println("RFID module found and initialized");
  }
}

void initializeLCD() {
  lcd.begin();
  lcd.backlight();
  Serial.println("LCD initialized");
}

void loop() {
  checkUltrasonic();
  checkSerialCommands();
  
  if (objectDetected) {
    showReadyForRFID();
    
    if (mfrc522.PICC_IsNewCardPresent() && mfrc522.PICC_ReadCardSerial()) {
      processRFIDScan();
    }
  } else {
    showApproachMessage();
  }
  
  mfrc522.PICC_HaltA();
  delay(200);
}

void checkUltrasonic() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  long duration = pulseIn(ECHO_PIN, HIGH);
  float distance = duration * 0.034 / 2;
  
  bool previousState = objectDetected;
  objectDetected = (distance > 0 && distance < 25);
  
  if (objectDetected && !previousState) {
    Serial.println("OBJECT_DETECTED");
  }
}

void processRFIDScan() {
  if (millis() - lastScanTime < SCAN_DELAY) {
    lcdPrint("Please wait...", "Scan too soon");
    playErrorBeep();
    return;
  }
  
  String rfidUID = readRFIDUID();
  float objectTemp = mlx.readObjectTempC() + tempOffset;
  float ambientTemp = mlx.readAmbientTempC();
  
  // Validate temperature reading
  if (objectTemp < 20.0 || objectTemp > 45.0) {
    lcdPrint("Temp Error", "Rescan needed");
    playErrorBeep();
    return;
  }
  
  updateDisplay(objectTemp);
  sendSerialData(rfidUID, objectTemp, ambientTemp);
  playResultSound(objectTemp);
  
  lastScanTime = millis();
}

String readRFIDUID() {
  String uid = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    uid += String(mfrc522.uid.uidByte[i] < 0x10 ? "0" : "");
    uid += String(mfrc522.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();
  return uid;
}

void updateDisplay(float temperature) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Temp: ");
  lcd.print(temperature, 1);
  lcd.print("C");
  
  lcd.setCursor(0, 1);
  if (temperature >= feverThreshold) {
    lcd.print("FEVER! ACCESS DENY");
  } else {
    lcd.print("NORMAL - WELCOME");
  }
}

void sendSerialData(String rfid, float temp, float ambient) {
  StaticJsonDocument<256> doc;
  doc["rfid"] = rfid;
  doc["temperature"] = temp;
  doc["ambient"] = ambient;
  doc["timestamp"] = millis();
  doc["fever_threshold"] = feverThreshold;
  doc["status"] = (temp >= feverThreshold) ? "fever" : "normal";
  
  String jsonString;
  serializeJson(doc, jsonString);
  Serial.println(jsonString);
}

void checkSerialCommands() {
  while (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    Serial.print("DEBUG: Received command: ");
    Serial.println(command);
    
    if (command == "BUZZER_TEST") {
      Serial.println("DEBUG: Executing BUZZER_TEST");
      buzzerTest();
    } else if (command == "LCD_TEST") {
      Serial.println("DEBUG: Executing LCD_TEST");
      lcdTest();
    } else if (command == "FEVER_ALERT") {
      Serial.println("DEBUG: Executing FEVER_ALERT");
      playFeverAlert();
    } else if (command == "SUCCESS_BEEP") {
      Serial.println("DEBUG: Executing SUCCESS_BEEP");
      playSuccessBeep();
    } else if (command == "CALIBRATE") {
      Serial.println("DEBUG: Executing CALIBRATE");
      calibrateSensor();
    } else if (command.startsWith("THRESHOLD:")) {
      Serial.println("DEBUG: Executing THRESHOLD update");
      setThreshold(command.substring(10));
    } else {
      Serial.println("DEBUG: Unknown command");
    }
  }
}

void setThreshold(String thresholdStr) {
  float newThreshold = thresholdStr.toFloat();
  if (newThreshold >= 35.0 && newThreshold <= 42.0) {
    feverThreshold = newThreshold;
    Serial.print("THRESHOLD_UPDATED:");
    Serial.println(feverThreshold);
    
    lcdPrint("Threshold Updated", String(feverThreshold) + "C");
    delay(2000);
    showReadyScreen();
  }
}

void calibrateSensor() {
  lcdPrint("Calibrating...", "Keep sensor clear");
  delay(2000);
  
  float ambient = mlx.readAmbientTempC();
  float object = mlx.readObjectTempC();
  
  // If object temp is close to ambient, assume no object
  if (abs(object - ambient) < 2.0) {
    tempOffset = 0.0; // Reset offset
    lcdPrint("Calibration", "Complete - Reset");
  } else {
    lcdPrint("Calibration", "Failed - Object");
  }
  
  Serial.print("CALIBRATION: ambient=");
  Serial.print(ambient);
  Serial.print(", object=");
  Serial.println(object);
  
  delay(2000);
  showReadyScreen();
}

// SOUND FUNCTIONS - IMPROVED
void playResultSound(float temperature) {
  Serial.print("DEBUG: Playing result sound for temp: ");
  Serial.println(temperature);
  if (temperature >= feverThreshold) {
    playFeverAlert();
  } else {
    playSuccessBeep();
  }
}

void playSuccessBeep() {
  Serial.println("DEBUG: Playing success beep");
  tone(BUZZER_PIN, 1000, 200);
  delay(300); // Wait for tone to finish
  noTone(BUZZER_PIN);
}

void playFeverAlert() {
  Serial.println("DEBUG: Playing fever alert");
  for (int i = 0; i < 3; i++) {
    tone(BUZZER_PIN, 800, 300);
    delay(400);
    noTone(BUZZER_PIN);
  }
}

void playErrorBeep() {
  Serial.println("DEBUG: Playing error beep");
  tone(BUZZER_PIN, 400, 500);
  delay(600);
  noTone(BUZZER_PIN);
}

void playWelcomeTone() {
  Serial.println("DEBUG: Playing welcome tone");
  tone(BUZZER_PIN, 523, 100); // C5
  delay(120);
  noTone(BUZZER_PIN);
  tone(BUZZER_PIN, 659, 100); // E5
  delay(120);
  noTone(BUZZER_PIN);
  tone(BUZZER_PIN, 784, 200); // G5
  delay(220);
  noTone(BUZZER_PIN);
}

void buzzerTest() {
  Serial.println("DEBUG: Starting buzzer test");
  lcdPrint("Buzzer Test", "Running...");
  
  // Test different frequencies
  int frequencies[] = {500, 1000, 1500, 2000};
  for (int i = 0; i < 4; i++) {
    Serial.print("DEBUG: Playing frequency: ");
    Serial.println(frequencies[i]);
    tone(BUZZER_PIN, frequencies[i], 300);
    delay(500);
    noTone(BUZZER_PIN);
  }
  
  noTone(BUZZER_PIN); // Ensure buzzer is off
  lcdPrint("Buzzer Test", "Complete!");
  Serial.println("BUZZER_TEST_COMPLETE");
  delay(1000);
  showReadyScreen();
}

// LCD FUNCTIONS
void lcdPrint(String line1, String line2) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(line1);
  lcd.setCursor(0, 1);
  lcd.print(line2);
}

void showWelcomeScreen() {
  lcdPrint("AttemptDance", "System Ready");
  delay(2000);
  showReadyScreen();
}

void showReadyScreen() {
  lcdPrint("Ready to Scan", "Approach sensor");
}

void showApproachMessage() {
  lcdPrint("Please Approach", "Temperature Sensor");
}

void showReadyForRFID() {
  lcdPrint("Ready for RFID", "Scan your card");
}

void lcdTest() {
  lcdPrint("LCD Test", "Backlight Test");
  
  for (int i = 0; i < 3; i++) {
    lcd.noBacklight();
    delay(300);
    lcd.backlight();
    delay(300);
  }
  
  lcdPrint("LCD Test", "Character Test");
  delay(1000);
  
  lcd.clear();
  for (int i = 0; i < 16; i++) {
    lcd.setCursor(i, 0);
    lcd.write('*');
    lcd.setCursor(i, 1);
    lcd.write('*');
    delay(100);
  }
  
  lcdPrint("Test Complete", "System Ready");
  Serial.println("LCD_TEST_COMPLETE");
  delay(2000);
  showReadyScreen();
}
