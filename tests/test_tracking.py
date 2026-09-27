from snap_go.config import Calibration
from snap_go.tracking import Tracker, Detection, TrackConfig

def det(x,y,t=10): return Detection(x,y,.9,t)
def test_disabled_holds():
    tr=Tracker(Calibration()); assert tr.update(det(.9,.9),10)[2]=='disabled'
def test_stale_holds():
    tr=Tracker(Calibration()); tr.enabled=True; assert tr.update(det(.9,.9,1),10)[2]=='stale'
def test_deadband_holds():
    tr=Tracker(Calibration()); tr.enabled=True; p,t,r=tr.update(det(.53,.47),10); assert (p,t)==(90,90) and r=='tracking'
def test_moves_right_down():
    tr=Tracker(Calibration()); tr.enabled=True; p,t,_=tr.update(det(.9,.9),10); assert p>90 and t>90
def test_step_limited():
    tr=Tracker(Calibration(),TrackConfig(max_step_deg=2)); tr.enabled=True; p,t,_=tr.update(det(1,1),10); assert p==92 and t==92
def test_invert():
    tr=Tracker(Calibration(pan_invert=True,tilt_invert=True)); tr.enabled=True; p,t,_=tr.update(det(.9,.9),10); assert p<90 and t<90
def test_manual_clamped(): assert Tracker(Calibration()).manual(-5,999)==(30,135)
def test_center():
    tr=Tracker(Calibration(pan_center=88,tilt_center=92)); tr.manual(120,120); assert tr.center()==(88,92)
