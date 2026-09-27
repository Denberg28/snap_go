import json, pytest
from snap_go.protocol import encode_message, decode_message, crc32_payload

def test_roundtrip(): assert decode_message(encode_message({"a":1})) == {"a":1}
def test_crc_stable(): assert crc32_payload({"b":2,"a":1}) == crc32_payload({"a":1,"b":2})
def test_bad_json():
    with pytest.raises(Exception): decode_message("nope")
def test_missing_fields():
    with pytest.raises(ValueError): decode_message('{}')
def test_crc_rejected():
    with pytest.raises(ValueError): decode_message(json.dumps({"payload":{"a":1},"crc32":"00000000"}))
@pytest.mark.parametrize("v",[0,1,-1,3.14,"x",True,None,[1,2],{"x":1}])
def test_payload_values(v): assert decode_message(encode_message({"v":v}))["v"] == v
