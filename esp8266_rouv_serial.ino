#include <Arduino.h>
#include <ArduinoJson.h>
#include <AccelStepper.h>

// =========================
// ROUV ESP8266 SERIAL MOTOR CONTROLLER
// Driver DC: 2x HW-039 / BTS7960
// R_EN dan L_EN tiap modul dihubungkan ke +5V
// =========================


// ---------- PIN DC MOTOR via HW-039 ----------
#define L_RPWM D1
#define L_LPWM D2

#define R_RPWM D4
#define R_LPWM D5


// ---------- PIN STEPPER ----------
#define STP_STEP D7
#define STP_DIR  D0

AccelStepper stepper(AccelStepper::DRIVER, STP_STEP, STP_DIR);


// ---------- SERIAL ----------
static const uint32_t SERIAL_BAUD = 115200;
String serialBuffer;


// ---------- STATE ----------
int currentLeft  = 1500;
int currentRight = 1500;
bool stepperBusy = false;


// ---------- HELPER ----------
int clampInt(int v, int lo, int hi) {
  if (v < lo) return lo;
  if (v > hi) return hi;
  return v;
}


// Konversi 1000–2000 ke PWM 0–255
int servoToPwmMagnitude(int val) {
  val = clampInt(val, 1000, 2000);
  int delta = val - 1500;   // -500 .. +500
  int mag   = map(abs(delta), 0, 500, 0, 255);
  if (mag < 8) mag = 0;     // deadband kecil
  return clampInt(mag, 0, 255);
}


// Kontrol 1 motor BTS7960/HW-039
void setOneMotorBTS(int servoVal, uint8_t rpwmPin, uint8_t lpwmPin) {
  servoVal = clampInt(servoVal, 1000, 2000);
  int mag = servoToPwmMagnitude(servoVal);

  if (mag == 0) {
    analogWrite(rpwmPin, 0);
    analogWrite(lpwmPin, 0);
    return;
  }

  if (servoVal > 1500) {
    analogWrite(rpwmPin, mag);
    analogWrite(lpwmPin, 0);
  } else {
    analogWrite(rpwmPin, 0);
    analogWrite(lpwmPin, mag);
  }
}


void applyMove(int leftVal, int rightVal) {
  currentLeft  = clampInt(leftVal, 1000, 2000);
  currentRight = clampInt(rightVal, 1000, 2000);

  setOneMotorBTS(currentLeft,  L_RPWM, L_LPWM);
  setOneMotorBTS(currentRight, R_RPWM, R_LPWM);
}


void stopDcMotors() {
  currentLeft  = 1500;
  currentRight = 1500;

  analogWrite(L_RPWM, 0);
  analogWrite(L_LPWM, 0);
  analogWrite(R_RPWM, 0);
  analogWrite(R_LPWM, 0);
}


void stopAll() {
  stopDcMotors();
  stepper.stop();
  stepperBusy = false;
}


void sendStatus() {
  StaticJsonDocument<192> out;
  out["type"] = "status";
  out["left"] = currentLeft;
  out["right"] = currentRight;
  out["stepper_busy"] = stepperBusy;
  out["driver"] = "HW-039_R/L_EN_5V";
  serializeJson(out, Serial);
  Serial.println();
}


void sendAck(const char* cmd, bool ok, const char* msg = nullptr) {
  StaticJsonDocument<192> out;
  out["type"] = "ack";
  out["cmd"] = cmd;
  out["ok"] = ok;
  if (msg) out["msg"] = msg;
  serializeJson(out, Serial);
  Serial.println();
}


// Helper: speed 0..255 → servo style 1000..2000
int speedToServo(int speed, bool forward) {
  speed = clampInt(speed, 0, 255);
  if (forward) {
    return 1500 + map(speed, 0, 255, 0, 500);
  } else {
    return 1500 - map(speed, 0, 255, 0, 500);
  }
}


void handleCommand(const String& line) {
  StaticJsonDocument<256> doc;
  DeserializationError err = deserializeJson(doc, line);
  if (err) {
    sendAck("parse", false, "json_invalid");
    return;
  }

  // =========================
  // KOMPATIBILITAS DUA FORMAT
  // Lama  : {"cmd":"move", ...}
  // Baru  : {"type":"motor_command","command":"MOVE", ...}
  // =========================
  String cmd = "";

  if (doc.containsKey("cmd")) {
    cmd = String((const char*)doc["cmd"]);
  } else if (doc.containsKey("command")) {
    cmd = String((const char*)doc["command"]);
    cmd.toLowerCase();
  }

  cmd.trim();

  // ---------- MOVE ----------
  if (cmd == "move") {
    int left  = doc["left"]  | 1500;
    int right = doc["right"] | 1500;
    applyMove(left, right);
    sendAck("move", true);
    return;
  }

  // ---------- STOP ----------
  if (cmd == "stop") {
    stopAll();
    sendAck("stop", true);
    return;
  }

  // ---------- STATUS ----------
  if (cmd == "status") {
    sendStatus();
    return;
  }

  // ---------- FORWARD ----------
  if (cmd == "forward") {
    int speed = doc["speed"] | 200;
    int val = speedToServo(speed, true);
    applyMove(val, val);
    sendAck("forward", true);
    return;
  }

  // ---------- BACKWARD ----------
  if (cmd == "backward") {
    int speed = doc["speed"] | 200;
    int val = speedToServo(speed, false);
    applyMove(val, val);
    sendAck("backward", true);
    return;
  }

  // ---------- TURN_LEFT ----------
  if (cmd == "turn_left") {
    int speed = doc["speed"] | 200;
    int leftVal  = speedToServo(speed, false);
    int rightVal = speedToServo(speed, true);
    applyMove(leftVal, rightVal);
    sendAck("turn_left", true);
    return;
  }

  // ---------- TURN_RIGHT ----------
  if (cmd == "turn_right") {
    int speed = doc["speed"] | 200;
    int leftVal  = speedToServo(speed, true);
    int rightVal = speedToServo(speed, false);
    applyMove(leftVal, rightVal);
    sendAck("turn_right", true);
    return;
  }

  // ---------- STEPPER ----------
  if (cmd == "stepper") {
  long steps = doc["steps"] | 200;
  int dir    = doc["dir"]   | 1;
  int speed  = doc["speed"] | 500;

  if (steps < 1) steps = 1;
  if (steps > 20000) steps = 20000;

  if (dir != -1 && dir != 1) dir = 1;
  speed = clampInt(speed, 1, 1200);

  stepper.setMaxSpeed(speed);
  stepper.setAcceleration(600);
  stepper.move(steps * dir);
  stepperBusy = true;
  sendAck("stepper", true);
  return;
}

  // ---------- STEPPER STOP ----------
  if (cmd == "stepper_stop") {
    stepper.stop();
    stepperBusy = false;
    sendAck("stepper_stop", true);
    return;
  }

  sendAck(cmd.c_str(), false, "unknown_cmd");
}


void setupMotorPins() {
  pinMode(L_RPWM, OUTPUT);
  pinMode(L_LPWM, OUTPUT);
  pinMode(R_RPWM, OUTPUT);
  pinMode(R_LPWM, OUTPUT);

  analogWriteRange(255);
  analogWriteFreq(1000);

  stopDcMotors();
}


void setupStepper() {
  pinMode(STP_STEP, OUTPUT);
  pinMode(STP_DIR, OUTPUT);
  stepper.setMaxSpeed(500);
  stepper.setAcceleration(600);
}


void setup() {
  Serial.begin(SERIAL_BAUD);
  serialBuffer.reserve(256);

  setupMotorPins();
  setupStepper();

  delay(300);
  sendAck("boot", true, "esp8266_hw039_ready");
}


void loop() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();

    if (c == '\n') {
      serialBuffer.trim();
      if (serialBuffer.length() > 0) {
        handleCommand(serialBuffer);
      }
      serialBuffer = "";
    } else if (c != '\r') {
      serialBuffer += c;
    }
  }

  stepper.run();

  if (stepperBusy && stepper.distanceToGo() == 0) {
    stepperBusy = false;
    sendAck("stepper_done", true);
  }
}