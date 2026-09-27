#include <Arduino.h>
#include <esp_task_wdt.h>
#include "protocol.h"
// Snap_Go 0.11.2. UART0 via DevKit USB-to-UART connector, not native USB CDC.
constexpr uint8_t PAN_PIN=5, TILT_PIN=6, STOP_PIN=7;
constexpr uint8_t F1_PIN=8, F2_PIN=9, F3_PIN=10;
constexpr uint16_t FUNCTION_US=1500;
snap::Guard guard;
uint8_t buffer[snap::SIZE]; size_t used=0;
uint32_t lastTick=0;
bool pwmStarted=false;
void pwm(uint8_t channel,uint16_t us) { ledcWrite(channel, uint32_t(us)*65535UL/20000UL); }
void functionPwm(uint8_t channel, bool on) { ledcWrite(channel, on ? uint32_t(FUNCTION_US)*65535UL/20000UL : 0); }
void setup() {
  pinMode(STOP_PIN, INPUT_PULLUP);
  for(uint8_t ch=0;ch<5;ch++) ledcSetup(ch,50,16);
  ledcAttachPin(PAN_PIN,0);ledcAttachPin(TILT_PIN,1);
  ledcAttachPin(F1_PIN,2);ledcAttachPin(F2_PIN,3);ledcAttachPin(F3_PIN,4);
  for(uint8_t ch=0;ch<5;ch++) ledcWrite(ch,0);
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
          snap::ack(reply,cmd.seq,guard.pan,guard.tilt,guard.flags());
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
    functionPwm(2,guard.functions&snap::F1);
    functionPwm(3,guard.functions&snap::F2);
    functionPwm(4,guard.functions&snap::F3);
  }
  delay(1);
}
