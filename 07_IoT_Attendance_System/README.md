IoT Contactless Attendance & Temperature Scanner

### 🚀 Overview
A hardware-based safety system developed for the post-pandemic era. It utilizes RFID technology for quick identification and infrared sensors for contactless temperature screening. This device ensures that only healthy, authorized individuals can enter a facility.

### 🔌 Hardware Components
* **Microcontroller:** Arduino / ESP32
* **Sensors:** MLX90614 (Contactless Temperature), RC522 (RFID Reader)
* **Display:** I2C LCD Screen (16x2)
* **Output:** Piezo Buzzer for alerts

### 📝 Functionality
1.  **Scan:** User taps their ID card (RFID) on the sensor.
2.  **Measure:** System simultaneously reads body temperature via IR sensor.
3.  **Decision:**
    * If temp is **< 37.5°C**: Access Granted (Green LED + Welcome Message).
    * If temp is **> 37.5°C**: Access Denied (Red LED + Alarm).

### 📸 Wiring & Prototype
