#include <Arduino.h>
#include <ESP32Servo.h>
#include <ArduinoJson.h>

#ifndef PAN_PIN
#define PAN_PIN 17
#endif
#ifndef TILT_PIN
#define TILT_PIN 18
#endif
#ifndef PAN_MIN_DEG
#define PAN_MIN_DEG 30
#endif
#ifndef PAN_MAX_DEG
#define PAN_MAX_DEG 150
#endif
#ifndef TILT_MIN_DEG
#define TILT_MIN_DEG 45
#endif
#ifndef TILT_MAX_DEG
#define TILT_MAX_DEG 135
#endif
#ifndef COMMAND_TIMEOUT_MS
#define COMMAND_TIMEOUT_MS 500
#endif

Servo panServo, tiltServo;
bool attached = false;
uint32_t lastValidMs = 0;

uint32_t crc32(const uint8_t *data, size_t len) {
  uint32_t crc = 0xFFFFFFFF;
  while (len--) {
    crc ^= *data++;
    for (uint8_t k=0;k<8;k++) crc = (crc>>1) ^ (0xEDB88320 & (-(int32_t)(crc&1)));
  }
  return ~crc;
}

String servoMaterial(JsonObject p) {
  return "servo|" + String(p["seq"].as<uint32_t>()) + "|" +
         String(p["pan"].as<float>(),2) + "|" + String(p["tilt"].as<float>(),2) + "|" +
         String((p["output"] | false) ? "1" : "0");
}

String crcHex(const String &material) {
  char out[9];
  snprintf(out,sizeof(out),"%08lx",(unsigned long)crc32((const uint8_t*)material.c_str(),material.length()));
  return String(out);
}

void sendAck(uint32_t seq) {
  String payload = "{\"seq\":" + String(seq) + ",\"type\":\"ack\"}";
  String material = "ack|" + String(seq);
  Serial.println("{\"payload\":" + payload + ",\"crc32\":\"" + crcHex(material) + "\"}");
}

void detachServos(){ if(attached){ panServo.detach(); tiltServo.detach(); attached=false; } }
void attachServos(){ if(!attached){ panServo.attach(PAN_PIN,500,2500); tiltServo.attach(TILT_PIN,500,2500); attached=true; } }

void setup(){ Serial.begin(115200); detachServos(); }

void loop(){
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    JsonDocument doc;
    if (deserializeJson(doc,line)==DeserializationError::Ok && doc["payload"].is<JsonObject>() && doc["crc32"].is<const char*>()) {
      JsonObject p=doc["payload"];
      if (p["type"]=="servo") {
        String material=servoMaterial(p);
        if (crcHex(material).equalsIgnoreCase(doc["crc32"].as<const char*>())) {
          lastValidMs=millis();
          bool out=p["output"]|false;
          if(out){
            attachServos();
            panServo.write(constrain(p["pan"].as<float>(),PAN_MIN_DEG,PAN_MAX_DEG));
            tiltServo.write(constrain(p["tilt"].as<float>(),TILT_MIN_DEG,TILT_MAX_DEG));
          } else detachServos();
          sendAck(p["seq"].as<uint32_t>());
        }
      }
    }
  }
  if(attached && millis()-lastValidMs > COMMAND_TIMEOUT_MS) detachServos();
}
