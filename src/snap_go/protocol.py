from __future__ import annotations
import json
import zlib

def crc_material(payload: dict) -> str:
    kind = payload.get("type")
    if kind == "servo":
        return f"servo|{int(payload['seq'])}|{float(payload['pan']):.2f}|{float(payload['tilt']):.2f}|{1 if payload.get('output') else 0}"
    if kind == "ack":
        return f"ack|{int(payload['seq'])}"
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))

def crc32_payload(payload: dict) -> str:
    return f"{zlib.crc32(crc_material(payload).encode()) & 0xffffffff:08x}"

def encode_message(payload: dict) -> bytes:
    envelope = {"payload": payload, "crc32": crc32_payload(payload)}
    return (json.dumps(envelope, separators=(",", ":")) + "\n").encode()

def decode_message(line: bytes | str) -> dict:
    if isinstance(line, bytes):
        line = line.decode("utf-8")
    obj = json.loads(line)
    if not isinstance(obj, dict) or "payload" not in obj or "crc32" not in obj:
        raise ValueError("invalid envelope")
    payload = obj["payload"]
    if not isinstance(payload, dict) or crc32_payload(payload) != str(obj["crc32"]).lower():
        raise ValueError("crc mismatch")
    return payload
