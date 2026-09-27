# Snap_Go serial protocol1

115200 baud,8N1, UART0 via USB bridge. Every packet is16 bytes, little endian.

| Offset | Bytes | Field |
|---:|---:|---|
| 0 | 2 | ASCII SG |
| 2 | 1 | Protocol version1 |
| 3 | 1 | Type1 command /2 acknowledgement |
| 4 | 4 | Sequence, unsigned32 |
| 8 | 2 | Pan pulse microseconds |
| 10 | 2 | Tilt pulse microseconds |
| 12 | 1 | Bit0 enabled; ACK bit1 fault |
| 13 | 1 | Reserved0 |
| 14 | 2 | CRC-16/CCITT-FALSE of bytes0–13; init0xffff, polynomial0x1021 |

Invalid version/type/reserved/CRC/ranges do not refresh the firmware watchdog. First send disabled to synchronize. Enabled sequences must move forward by1..2^31−1 modulo2^32; replay/old commands do not refresh. Disabled commands may resynchronize any sequence and only hold. Firmware timeout or STOP requires another valid disabled handshake, followed by explicit host enable. ACK reports commanded current PWM before that loop's slew step. PWM updates50Hz; serial host20Hz. No ACK means host disarms, rather than assuming a write means delivery.

Frames are bounded; parsers resynchronize bytewise after corruption. The firmware reads at most64 bytes per main-loop pass. No text/debug shares the protocol after boot. Boot ROM text is ignored by the framing parser. The protocol does not provide authentication/encryption; use a physical trusted USB link.
