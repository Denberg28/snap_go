#include "protocol.h"
#include <assert.h>
#include <stdio.h>
int main() {
  using namespace snap;
  assert(crc((const uint8_t*)"123456789",9)==0x29b1);
  Guard g;Command off{1,1500,1500,false},on{2,1900,1100,true};
  assert(!g.accept(on,0,false)); // boot refuses enabled packets
  assert(g.accept(off,0,false));assert(g.accept(on,1,false));
  assert(!g.accept(on,2,false)); // replay cannot refresh watchdog
  g.step();assert(g.pan==1504&&g.tilt==1496);
  g.check(352,false);assert(!g.enabled&&g.fault&&!g.synced);
  on.seq=3;assert(!g.accept(on,353,false));
  off.seq=4;assert(g.accept(off,354,false));on.seq=5;assert(g.accept(on,355,false));
  g.check(356,true);assert(!g.enabled&&g.fault);
  off.seq=6;g.accept(off,357,true);on.seq=7;assert(!g.accept(on,358,false));
  g.accept(off,359,false);assert(g.accept(on,360,false));
  for(int i=0;i<1000;i++){g.step();}
  assert(g.pan==1900&&g.tilt==1100);
  Guard wrap;off.seq=0xffffffff;wrap.accept(off,0xfffffff0,false);on.seq=0;
  assert(wrap.accept(on,0xfffffff5,false));wrap.check(20,false);assert(wrap.enabled);
  wrap.check(400,false);assert(!wrap.enabled);
  uint8_t packet[16];ack(packet,0x12345678,1500,1600,1);
  for(auto x:packet){printf("%02x",x);}
  puts("");
}
