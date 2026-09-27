from snap_go.config import Calibration
from snap_go.tracking import Tracker, Detection
from snap_go.runtime import TrackingRuntime
from snap_go.protocol import decode_message, encode_message
from snap_go.link import ServoLink
class Src:
    def __init__(self,d): self.d=d
    def next_detection(self): return self.d
class BadSrc:
    def next_detection(self): raise RuntimeError('camera')
class Serial:
    def __init__(self): self.buf=b''
    def write(self,d): self.buf=d; return len(d)
    def readline(self): return encode_message({'type':'ack','seq':decode_message(self.buf)['seq']})
def test_runtime_tracks():
    tr=Tracker(Calibration()); tr.enabled=True; rt=TrackingRuntime(tr,Src(Detection(.9,.5,.9,10)),ServoLink(Serial())); s=rt.step(10); assert s.commands==1 and s.last_reason=='tracking'
def test_runtime_disabled_no_command():
    rt=TrackingRuntime(Tracker(Calibration()),Src(None),ServoLink(Serial())); assert rt.step(10).commands==0
def test_runtime_fault_disables_tracking():
    tr=Tracker(Calibration()); tr.enabled=True; s=TrackingRuntime(tr,BadSrc(),ServoLink(Serial())).step(10); assert not tr.enabled and s.last_reason=='fault'
