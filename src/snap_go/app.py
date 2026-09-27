from __future__ import annotations
import os
from flask import Flask, jsonify, request
from .config import CalibrationStore
from .tracking import Tracker

HTML='''<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Snap_Go</title><style>body{font-family:system-ui;max-width:720px;margin:auto;padding:18px;background:#111;color:#eee}button,input{font-size:16px;padding:10px;margin:4px}.card{background:#1c1c1c;border-radius:14px;padding:14px;margin:10px 0}#status{white-space:pre-wrap}</style><h1>Snap_Go</h1><div class=card><button onclick="post('/api/tracking',{enabled:true})">Track ON</button><button onclick="post('/api/tracking',{enabled:false})">Track OFF</button><button onclick="post('/api/center',{})">Center</button><button onclick="post('/api/release',{})">Release servos</button></div><div class=card>Pan <input id=p type=range min=0 max=180 value=90> Tilt <input id=t type=range min=0 max=180 value=90><button onclick="post('/api/manual',{pan:+p.value,tilt:+t.value})">Move</button></div><div class=card id=status></div><script>async function post(u,b){await fetch(u,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(b)});refresh()}async function refresh(){status.textContent=JSON.stringify(await (await fetch('/api/status')).json(),null,2)}setInterval(refresh,1000);refresh()</script>'''

def create_app(config_path: str | None = None) -> Flask:
    app=Flask(__name__)
    store=CalibrationStore(config_path or os.getenv("SNAP_GO_CONFIG","data/calibration.json"))
    tracker=Tracker(store.load())
    state={"tracking":False,"output_enabled":False,"pan":tracker.pan,"tilt":tracker.tilt,"last_reason":"boot","link":"not-configured"}
    app.config["tracker"]=tracker
    app.config["state"]=state
    app.config["store"]=store

    @app.get("/")
    def index(): return HTML

    @app.get("/api/status")
    def status(): return jsonify(state)

    @app.post("/api/tracking")
    def tracking():
        tracker.enabled=bool((request.get_json(silent=True) or {}).get("enabled",False))
        state["tracking"]=tracker.enabled
        state["output_enabled"]=True
        return jsonify(state)

    @app.post("/api/manual")
    def manual():
        d=request.get_json(force=True)
        p,t=tracker.manual(float(d["pan"]),float(d["tilt"]))
        state.update(pan=p,tilt=t,output_enabled=True,last_reason="manual")
        return jsonify(state)

    @app.post("/api/center")
    def center():
        p,t=tracker.center()
        state.update(pan=p,tilt=t,output_enabled=True,last_reason="center")
        return jsonify(state)

    @app.post("/api/release")
    def release():
        state["output_enabled"]=False
        state["tracking"]=False
        tracker.enabled=False
        return jsonify(state)
    return app

def main():
    create_app().run(host=os.getenv("SNAP_GO_HOST","0.0.0.0"),port=int(os.getenv("SNAP_GO_PORT","8080")),debug=False)
