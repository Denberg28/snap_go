#pragma once
#include <stdint.h>
#include <stddef.h>
#include <string.h>
namespace snap {
constexpr uint8_t VERSION = 1;
constexpr size_t SIZE = 16;
inline uint16_t crc(const uint8_t* p, size_t n) {
  uint16_t c = 0xffff;
  while (n--) { c ^= uint16_t(*p++) << 8; for (int i=0;i<8;i++) c = (c & 0x8000) ? (c << 1)^0x1021 : c << 1; }
  return c;
}
inline uint16_t u16(const uint8_t* p) { return p[0] | uint16_t(p[1]) << 8; }
inline uint32_t u32(const uint8_t* p) { return p[0] | uint32_t(p[1])<<8 | uint32_t(p[2])<<16 | uint32_t(p[3])<<24; }
inline void put16(uint8_t* p, uint16_t v) { p[0]=v; p[1]=v>>8; }
inline void put32(uint8_t* p, uint32_t v) { for(int i=0;i<4;i++) p[i]=v>>(8*i); }
struct Command { uint32_t seq; uint16_t pan, tilt; bool enabled; };
inline bool decode(const uint8_t* p, Command& cmd) {
  if(p[0]!='S'||p[1]!='G'||p[2]!=VERSION||p[3]!=1||p[13]!=0||p[12]>1||u16(p+14)!=crc(p,14)) return false;
  cmd={u32(p+4),u16(p+8),u16(p+10),bool(p[12])};
  return cmd.pan>=1100&&cmd.pan<=1900&&cmd.tilt>=1100&&cmd.tilt<=1900;
}
inline void ack(uint8_t* p, uint32_t seq, uint16_t pan, uint16_t tilt, uint8_t flags) {
  p[0]='S';p[1]='G';p[2]=VERSION;p[3]=2;
  put32(p+4,seq);put16(p+8,pan);put16(p+10,tilt);p[12]=flags;p[13]=0;put16(p+14,crc(p,14));
}
class Guard {
 public:
  bool enabled=false, fault=false, synced=false;
  uint32_t last=0, seq=0;
  uint16_t pan=1500, tilt=1500, targetPan=1500, targetTilt=1500;
  bool accept(const Command& c, uint32_t now, bool stop) {
    if(!c.enabled) {
      enabled=false; fault=stop; synced=!stop; seq=c.seq; last=now;
      targetPan=pan;targetTilt=tilt;return true;
    }
    uint32_t advance=c.seq-seq;
    if(stop||!synced||fault||advance==0||advance>=0x80000000UL) return false;
    seq=c.seq;last=now;enabled=true;targetPan=c.pan;targetTilt=c.tilt;return true;
  }
  void check(uint32_t now, bool stop) {
    if(stop||(synced&&uint32_t(now-last)>350)) {
      enabled=false;fault=true;synced=false;targetPan=pan;targetTilt=tilt;
    }
  }
  void step() { // exactly every 20 ms: 4 us / tick == 200 us/s, no catch-up
    if(!enabled) return;
    pan=advance(pan,targetPan);tilt=advance(tilt,targetTilt);
  }
 private:
  static uint16_t advance(uint16_t a,uint16_t b) {
    return b>a ? a+((b-a)>4?4:b-a) : a-((a-b)>4?4:a-b);
  }
};
}
