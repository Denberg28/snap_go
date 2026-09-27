import pytest
from snap_go.config import Calibration
from snap_go.tracking import Tracker
from snap_go.controller import SnapGoController

class Link:
    def __init__(self, fail=False): self.calls=[]; self.fail=fail
    def command(self,p,t,output):
        if self.fail: raise RuntimeError('serial')
        self.calls.append((p,t,output)); return {'type':'ack','seq':1}

def test_manual_commands_servo_and_disables_tracking():
    tr=Tracker(Calibration()); tr.enabled=True; l=Link(); c=SnapGoController(tr,l)
    s=c.manual(100,80); assert l.calls[-1]==(100,80,True) and not s['tracking'] and s['output_enabled']
def test_center_commands_servo():
    l=Link(); c=SnapGoController(Tracker(Calibration()),l); c.center(); assert l.calls[-1]==(90,90,True)
def test_release_detaches_output():
    l=Link(); c=SnapGoController(Tracker(Calibration()),l); s=c.release(); assert l.calls[-1][2] is False and not s['output_enabled']
def test_link_fault_disables_tracking():
    tr=Tracker(Calibration()); tr.enabled=True; c=SnapGoController(tr,Link(True))
    with pytest.raises(RuntimeError): c.manual(90,90)
    assert not c.status.tracking and c.status.link=='fault'
def test_no_link_is_safe_for_ui_preview():
    s=SnapGoController(Tracker(Calibration())).manual(100,80); assert s['link']=='not-configured' and s['output_enabled']
