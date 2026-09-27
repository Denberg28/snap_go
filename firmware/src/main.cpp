#include <Arduino.h>
#include <esp_task_wdt.h>
#include "protocol.h"
// Snap_Go 0.8.0. UART0 via DevKit USB-to-UART connector, not native USB CDC.
constexpr uint8_t PAN_PIN=5, TILT_PIN=6, STOP_PIN=7;
snap::Guard guard;
uint8_t buffer[snap::SIZE]; size_t used=0;
uint32_t lastTick=0;
bool pwmStarted=false;
void pwm(uint8_t channel,uint16_t us) { ledcWrite(channel, uint32_t(us)*65535UL/20000UL); }
void setup() {
  pinMode(STOP_PIN, INPUT_PULLUP);
  ledcSetup(0,50,16);ledcSetup(1,50,16);
  ledcAttachPin(PAN_PIN,0);ledcAttachPin(TILT_PIN,1);
  ledcWrite(0,0);ledcWrite(1,0); // no pulses before explicit enable
  Serial.begin(115200);
  esp_task_wdt_init(2,true);esp_task_wdt_add(nullptr);
}
void loop() {
  esp_task_wdt_reset();
  uint32_t now=millis(); bool stop=digitalRead(STOP_PIN)==LOW;
  guard.check(now,stop);
  for(int budget=64;budget>0&&Serial.available();--budget) {
    buffer[used++]=uint8_t(Serial.read());
    if(used==snap::SIZE) {
      snap::Command cmd;
      if(snap::decode(buffer,cmd)) {
        if(guard.accept(cmd,now,stop)) {
          uint8_t reply[snap::SIZE];
          snap::ack(reply,cmd.seq,guard.pan,guard.tilt,(guard.enabled?1:0)|(guard.fault?2:0));
          if(Serial.availableForWrite()>=int(snap::SIZE)) Serial.write(reply,snap::SIZE);
        }
        used=0;
      } else { memmove(buffer,buffer+1,snap::SIZE-1);used=snap::SIZE-1; }
    }
  }
  if(uint32_t(now-lastTick)>=20) {
    lastTick=now;guard.step();
    if(guard.enabled) pwmStarted=true;
    if(pwmStarted) { pwm(0,guard.pan);pwm(1,guard.tilt); }
  }
  delay(1);
}
