import pytest
from snap_go.config import Calibration, CalibrationStore

def test_default_valid(): Calibration().validate()
@pytest.mark.parametrize("p,t,expected",[(0,0,(30,45)),(180,180,(150,135)),(90,90,(90,90)),(42,133,(42,133))])
def test_clamp(p,t,expected): assert Calibration().clamp(p,t)==expected
@pytest.mark.parametrize("kwargs",[{"pan_min":100,"pan_max":90},{"tilt_min":100,"tilt_max":90},{"pan_center":20},{"tilt_center":140}])
def test_invalid(kwargs):
    with pytest.raises(ValueError): Calibration(**kwargs).validate()
def test_store_roundtrip(tmp_path):
    s=CalibrationStore(tmp_path/'c.json'); c=Calibration(pan_center=91); s.save(c); assert s.load().pan_center==91
def test_store_default(tmp_path): assert CalibrationStore(tmp_path/'x').load()==Calibration()
