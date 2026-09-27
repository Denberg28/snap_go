import pytest
from snap_go.link import ServoLink
from snap_go.protocol import decode_message, encode_message
class Fake:
    def __init__(self,bad=False): self.written=b''; self.bad=bad
    def write(self,d): self.written=d; return len(d)
    def readline(self):
        p=decode_message(self.written); return encode_message({"type":"ack","seq":999 if self.bad else p['seq']})
def test_command_ack():
    f=Fake(); l=ServoLink(f); a=l.command(90,91); assert a['seq']==1 and decode_message(f.written)['output'] is True
def test_bad_ack():
    with pytest.raises(ValueError): ServoLink(Fake(True)).command(90,90)
def test_seq_increments():
    f=Fake(); l=ServoLink(f); l.command(1,2); l.command(3,4); assert l.seq==2
