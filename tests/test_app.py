from snap_go.app import create_app

def client(tmp_path): return create_app(str(tmp_path/'c.json')).test_client()
def test_status_boot(tmp_path):
    j=client(tmp_path).get('/api/status').get_json(); assert j['tracking'] is False and j['output_enabled'] is False
def test_tracking_enable(tmp_path): assert client(tmp_path).post('/api/tracking',json={'enabled':True}).get_json()['tracking'] is True
def test_manual_enables_output(tmp_path):
    j=client(tmp_path).post('/api/manual',json={'pan':100,'tilt':80}).get_json(); assert j['output_enabled'] and (j['pan'],j['tilt'])==(100,80)
def test_center_enables_output(tmp_path): assert client(tmp_path).post('/api/center',json={}).get_json()['output_enabled'] is True
def test_release_disables(tmp_path):
    c=client(tmp_path); c.post('/api/tracking',json={'enabled':True}); j=c.post('/api/release',json={}).get_json(); assert not j['tracking'] and not j['output_enabled']
