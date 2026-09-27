from __future__ import annotations
import os
from flask import Flask, jsonify, request
from . import __version__
from .config import CalibrationStore
from .tracking import Tracker
from .controller import SnapGoController

RELEASE_URL = "https://github.com/Denberg28/snap_go/releases/latest"

HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Snap_Go</title>
<style>
:root{color-scheme:dark;--bg:#080a0d;--panel:#101419;--panel2:#151b22;--line:#29313a;--text:#eef2f5;--muted:#87929d;--accent:#d9f99d;--warn:#f6c177;--danger:#ff7a7a}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0;width:100%;height:100%;background:var(--bg);color:var(--text);font-family:Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif;overflow:hidden}
button,input{font:inherit}
button{border:1px solid var(--line);background:var(--panel2);color:var(--text);border-radius:10px;padding:8px 11px;cursor:pointer}
button:active{transform:translateY(1px)}
button.primary{background:var(--accent);color:#111;border-color:transparent;font-weight:700}
button.danger{color:#ffd7d7;border-color:#5f3232;background:#241416}
.shell{height:100svh;display:grid;grid-template-rows:48px minmax(0,1fr) 46px;gap:0}
.topbar,.bottombar{display:flex;align-items:center;gap:8px;padding:6px 10px;background:#0b0e12;border-color:var(--line);z-index:5}
.topbar{border-bottom:1px solid var(--line)}
.bottombar{border-top:1px solid var(--line)}
.brand{display:flex;align-items:baseline;gap:7px;min-width:max-content}
.brand strong{font-size:15px;letter-spacing:.03em}
.brand small{font-size:10px;color:var(--muted)}
.spacer{flex:1}
.segment{display:flex;padding:2px;border:1px solid var(--line);border-radius:10px;background:#080a0d}
.segment button{padding:5px 10px;border:0;background:transparent;color:var(--muted);border-radius:7px;font-size:12px}
.segment button.active{background:#232a32;color:var(--text)}
.iconbtn{padding:6px 9px;font-size:12px}
.workspace{display:grid;grid-template-columns:112px minmax(0,1fr) 112px;gap:10px;padding:10px;min-height:0}
.side{display:flex;flex-direction:column;justify-content:center;align-items:center;gap:10px;min-width:0}
.axis-title{font-size:10px;letter-spacing:.14em;color:var(--muted);font-weight:700}
.joy{width:98px;height:98px;border:1px solid var(--line);border-radius:50%;position:relative;background:radial-gradient(circle at center,#171c22 0 16%,#0d1116 17% 48%,#181e25 49% 50%,#0c0f13 51%);touch-action:none;user-select:none}
.joy:before,.joy:after{content:"";position:absolute;background:#313943;opacity:.7}
.joy.pan:before{left:13px;right:13px;top:48px;height:1px}
.joy.pan:after{display:none}
.joy.tilt:before{top:13px;bottom:13px;left:48px;width:1px}
.joy.tilt:after{display:none}
.knob{position:absolute;left:50%;top:50%;width:34px;height:34px;margin:-17px;border-radius:50%;background:#dde4ea;border:5px solid #343d47;box-shadow:0 3px 16px #0008;transition:transform .08s linear}
.axis-value{font-size:11px;color:var(--muted);font-variant-numeric:tabular-nums}
.stage{position:relative;min-width:0;min-height:0;border:1px solid var(--line);border-radius:14px;overflow:hidden;background:radial-gradient(circle at 50% 45%,#1a222b 0,#10161c 42%,#090c10 100%);box-shadow:0 12px 40px #0008}
.stage img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:none}
.gridlines{position:absolute;inset:0;background-image:linear-gradient(#ffffff08 1px,transparent 1px),linear-gradient(90deg,#ffffff08 1px,transparent 1px);background-size:12.5% 12.5%;pointer-events:none}
.crosshair{position:absolute;left:50%;top:50%;width:66px;height:66px;transform:translate(-50%,-50%);opacity:.8;pointer-events:none}
.crosshair:before,.crosshair:after{content:"";position:absolute;background:#e9eef3aa}
.crosshair:before{left:32px;top:0;width:1px;height:66px}
.crosshair:after{left:0;top:32px;width:66px;height:1px}
.centerbox{position:absolute;left:40%;top:40%;width:20%;height:20%;border:1px dashed #d9f99d55;border-radius:8px;pointer-events:none}
.target{position:absolute;width:72px;height:112px;border:2px solid var(--accent);border-radius:8px;transform:translate(-50%,-50%);box-shadow:0 0 0 1px #0008;display:none;pointer-events:none}
.target:after{content:"PERSON 0.94";position:absolute;left:-2px;top:-21px;font-size:9px;font-weight:800;letter-spacing:.06em;background:var(--accent);color:#111;padding:3px 5px;border-radius:5px}
.stage-status{position:absolute;left:10px;top:10px;display:flex;gap:6px;flex-wrap:wrap}
.chip{font-size:10px;padding:4px 7px;border:1px solid #ffffff18;border-radius:999px;background:#0a0d11c9;color:#c9d1d8;backdrop-filter:blur(8px)}
.chip.ok{color:var(--accent)}
.empty{position:absolute;inset:0;display:grid;place-items:center;text-align:center;color:var(--muted);font-size:12px;padding:20px}
.empty b{display:block;color:#cbd3da;margin-bottom:4px}
.testbar{position:absolute;left:50%;bottom:10px;transform:translateX(-50%);display:none;align-items:center;gap:6px;padding:5px;background:#080b0fd9;border:1px solid var(--line);border-radius:11px;backdrop-filter:blur(8px)}
.testbar button{font-size:10px;padding:5px 8px}
.testbar button.active{border-color:#67737e;color:var(--accent)}
.bottombar{font-size:11px}
.metric{display:flex;gap:4px;align-items:center;color:var(--muted);white-space:nowrap}
.metric b{color:var(--text);font-variant-numeric:tabular-nums}
.bottombar button{padding:6px 10px;font-size:11px}
.drawer{position:absolute;right:10px;top:56px;width:270px;background:#0f1419f2;border:1px solid var(--line);border-radius:14px;padding:12px;z-index:10;box-shadow:0 20px 60px #000b;backdrop-filter:blur(14px);display:none}
.drawer.open{display:block}
.drawer h3{font-size:12px;margin:0 0 12px}
.setting{margin:10px 0}
.setting label{display:flex;justify-content:space-between;font-size:10px;color:var(--muted);margin-bottom:6px}
.setting input[type=range]{width:100%;accent-color:#d9f99d}
.hint{font-size:10px;color:var(--muted);line-height:1.45}
.portrait{display:none}
@media (max-width:800px){.workspace{grid-template-columns:88px minmax(0,1fr) 88px;gap:6px;padding:6px}.joy{width:76px;height:76px}.knob{width:28px;height:28px;margin:-14px}.stage{border-radius:10px}.brand small{display:none}.metric.hide-sm{display:none}}
@media (orientation:portrait){.portrait{display:grid;position:fixed;inset:0;z-index:99;background:#080a0df2;place-items:center;text-align:center;padding:30px;color:#c9d1d8}.portrait b{display:block;font-size:18px;margin-bottom:6px}}
</style>
</head>
<body>
<div class="shell">
<header class="topbar">
  <div class="brand"><strong>Snap_Go</strong><small>v__VERSION__</small></div>
  <div class="chip" id="linkChip">LINK · --</div>
  <div class="spacer"></div>
  <div class="segment" aria-label="Mode">
    <button id="liveBtn" onclick="setMode('live')">LIVE</button>
    <button id="testBtn" class="active" onclick="setMode('test')">TEST</button>
  </div>
  <button class="iconbtn" onclick="toggleSettings()">SETTINGS</button>
  <button class="iconbtn" onclick="openUpdate()">UPDATE</button>
</header>

<main class="workspace">
  <section class="side">
    <div class="axis-title">PAN</div>
    <div class="joy pan" id="panJoy"><div class="knob" id="panKnob"></div></div>
    <div class="axis-value">LEFT / RIGHT</div>
  </section>

  <section class="stage" id="stage">
    <img id="liveFeed" alt="Live camera feed">
    <div class="gridlines"></div>
    <div class="centerbox"></div>
    <div class="crosshair"></div>
    <div class="target" id="target"></div>
    <div class="stage-status">
      <span class="chip" id="modeChip">TEST</span>
      <span class="chip ok" id="detectChip">DETECT · READY</span>
      <span class="chip" id="trackChip">TRACK · OFF</span>
    </div>
    <div class="empty" id="empty"><div><b>TEST VIEW</b>Pan/tilt controls are live; target motion is simulated.</div></div>
    <div class="testbar" id="testbar">
      <button id="stationaryBtn" onclick="setTargetMode('stationary')">STATIONARY</button>
      <button id="movingBtn" class="active" onclick="setTargetMode('moving')">MOVING</button>
    </div>
  </section>

  <section class="side">
    <div class="axis-title">TILT</div>
    <div class="joy tilt" id="tiltJoy"><div class="knob" id="tiltKnob"></div></div>
    <div class="axis-value">UP / DOWN</div>
  </section>
</main>

<footer class="bottombar">
  <button id="trackBtn" class="primary" onclick="toggleTracking()">TRACK ON</button>
  <button onclick="postAction('/api/center',{})">CENTER</button>
  <button class="danger" onclick="postAction('/api/release',{})">RELEASE</button>
  <div class="spacer"></div>
  <div class="metric">PAN <b id="panValue">90.0°</b></div>
  <div class="metric">TILT <b id="tiltValue">90.0°</b></div>
  <div class="metric hide-sm">STATE <b id="reasonValue">BOOT</b></div>
</footer>
</div>

<aside class="drawer" id="drawer">
  <h3>Pan / Tilt Setup</h3>
  <div class="setting"><label><span>Pan angle</span><span id="panSetValue">90°</span></label><input id="panSet" type="range" min="30" max="150" value="90"></div>
  <div class="setting"><label><span>Tilt angle</span><span id="tiltSetValue">90°</span></label><input id="tiltSet" type="range" min="45" max="135" value="90"></div>
  <button style="width:100%" onclick="applyManual()">MOVE TO ANGLES</button>
  <p class="hint" id="streamHint">Live stream: not configured</p>
  <p class="hint">Tracking starts OFF after restart. RELEASE detaches servo output on supported hardware.</p>
</aside>

<div class="portrait"><div><b>Rotate to landscape</b>Snap_Go is designed around the camera view.</div></div>

<script>
const S={mode:'test',targetMode:'moving',tracking:false,pan:90,tilt:90,link:'--',reason:'boot',streamUrl:'',releaseUrl:'https://github.com/Denberg28/snap_go/releases/latest',lastCommand:0};
const $=id=>document.getElementById(id);
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));

async function postAction(url,body){
  try{
    const r=await fetch(url,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});
    if(!r.ok) throw new Error('HTTP '+r.status);
    applyStatus(await r.json());
  }catch(e){
    $('linkChip').textContent='LINK · ERROR';
    $('linkChip').style.color='var(--danger)';
  }
}

function applyStatus(j){
  S.tracking=!!j.tracking; S.pan=Number(j.pan??S.pan); S.tilt=Number(j.tilt??S.tilt); S.link=j.link||'--'; S.reason=j.last_reason||'--';
  $('panValue').textContent=S.pan.toFixed(1)+'°'; $('tiltValue').textContent=S.tilt.toFixed(1)+'°';
  $('panSet').value=S.pan; $('tiltSet').value=S.tilt; $('panSetValue').textContent=Math.round(S.pan)+'°'; $('tiltSetValue').textContent=Math.round(S.tilt)+'°';
  $('reasonValue').textContent=String(S.reason).toUpperCase();
  $('linkChip').textContent='LINK · '+String(S.link).toUpperCase(); $('linkChip').style.color=S.link==='connected'?'var(--accent)':'';
  $('trackChip').textContent='TRACK · '+(S.tracking?'ON':'OFF'); $('trackChip').className='chip'+(S.tracking?' ok':'');
  $('trackBtn').textContent=S.tracking?'TRACK OFF':'TRACK ON'; $('trackBtn').className=S.tracking?'':'primary';
}

async function refresh(){
  try{const r=await fetch('/api/status'); if(r.ok) applyStatus(await r.json());}catch(_){}
}
async function loadConfig(){
  try{
    const r=await fetch('/api/ui-config'); if(!r.ok)return; const j=await r.json();
    S.streamUrl=j.stream_url||''; S.releaseUrl=j.release_url||S.releaseUrl;
    $('streamHint').textContent='Live stream: '+(S.streamUrl||'not configured');
  }catch(_){}
}

function setMode(mode){
  S.mode=mode;
  $('liveBtn').classList.toggle('active',mode==='live'); $('testBtn').classList.toggle('active',mode==='test');
  $('modeChip').textContent=mode.toUpperCase(); $('testbar').style.display=mode==='test'?'flex':'none';
  $('target').style.display=mode==='test'?'block':'none';
  if(mode==='live'){
    $('detectChip').textContent='DETECT · LIVE';
    if(S.streamUrl){$('liveFeed').src=S.streamUrl;$('liveFeed').style.display='block';$('empty').style.display='none';}
    else{$('liveFeed').style.display='none';$('empty').innerHTML='<div><b>LIVE CAMERA</b>Configure SNAP_GO_STREAM_URL on the Raspberry Pi.</div>';$('empty').style.display='grid';}
  }else{
    $('liveFeed').style.display='none'; $('detectChip').textContent='DETECT · READY';
    $('empty').innerHTML='<div><b>TEST VIEW</b>Pan/tilt controls are live; target motion is simulated.</div>'; $('empty').style.display='grid';
  }
}
function setTargetMode(mode){
  S.targetMode=mode; $('stationaryBtn').classList.toggle('active',mode==='stationary'); $('movingBtn').classList.toggle('active',mode==='moving');
}
function toggleTracking(){postAction('/api/tracking',{enabled:!S.tracking});}
function toggleSettings(){$('drawer').classList.toggle('open');}
function openUpdate(){window.open(S.releaseUrl,'_blank','noopener');}
function applyManual(){postAction('/api/manual',{pan:+$('panSet').value,tilt:+$('tiltSet').value});}
$('panSet').oninput=e=>$('panSetValue').textContent=e.target.value+'°';
$('tiltSet').oninput=e=>$('tiltSetValue').textContent=e.target.value+'°';

function bindAxis(baseId,knobId,axis){
  const base=$(baseId),knob=$(knobId); let active=false;
  const update=(ev,send)=>{
    const r=base.getBoundingClientRect(),cx=r.left+r.width/2,cy=r.top+r.height/2,limit=r.width*.31;
    let n=axis==='pan'?(ev.clientX-cx)/limit:(ev.clientY-cy)/limit; n=clamp(n,-1,1);
    knob.style.transform=axis==='pan'?('translateX('+(n*limit)+'px)'):('translateY('+(n*limit)+'px)');
    if(send && Date.now()-S.lastCommand>110){
      S.lastCommand=Date.now();
      const pan=axis==='pan'?clamp(S.pan+n*3.0,30,150):S.pan;
      const tilt=axis==='tilt'?clamp(S.tilt+n*3.0,45,135):S.tilt;
      postAction('/api/manual',{pan,tilt});
    }
  };
  base.addEventListener('pointerdown',e=>{active=true;base.setPointerCapture(e.pointerId);update(e,true)});
  base.addEventListener('pointermove',e=>{if(active)update(e,true)});
  const end=()=>{active=false;knob.style.transform='translate(0,0)'};
  base.addEventListener('pointerup',end); base.addEventListener('pointercancel',end);
}
bindAxis('panJoy','panKnob','pan'); bindAxis('tiltJoy','tiltKnob','tilt');

function animateTarget(ms){
  const t=ms/1000,target=$('target');
  if(S.mode==='test'){
    let x=50,y=50;
    if(S.targetMode==='moving'){
      const spread=S.tracking?2.8:24;
      x=50+Math.sin(t*.9)*spread; y=50+Math.cos(t*.67)*(S.tracking?1.8:15);
    }else{
      x=S.tracking?50+Math.sin(t*1.4)*.8:61;
      y=S.tracking?50+Math.cos(t*1.1)*.6:45;
    }
    target.style.left=x+'%'; target.style.top=y+'%';
    $('detectChip').textContent='DETECT · PERSON'; $('detectChip').className='chip ok';
  }
  requestAnimationFrame(animateTarget);
}

loadConfig().then(()=>setMode('test')); refresh(); setInterval(refresh,1000); requestAnimationFrame(animateTarget);
</script>
</body>
</html>"""

def create_app(config_path: str | None = None) -> Flask:
    app = Flask(__name__)
    store = CalibrationStore(config_path or os.getenv("SNAP_GO_CONFIG", "data/calibration.json"))
    tracker = Tracker(store.load())
    controller = SnapGoController(tracker)
    app.config["tracker"] = tracker
    app.config["controller"] = controller
    app.config["store"] = store

    @app.get("/")
    def index():
        return HTML.replace("__VERSION__", __version__)

    @app.get("/api/status")
    def status():
        return jsonify(controller.snapshot())

    @app.get("/api/ui-config")
    def ui_config():
        return jsonify(
            version=__version__,
            stream_url=os.getenv("SNAP_GO_STREAM_URL", "").strip(),
            release_url=RELEASE_URL,
        )

    @app.post("/api/tracking")
    def tracking():
        return jsonify(controller.set_tracking(bool((request.get_json(silent=True) or {}).get("enabled", False))))

    @app.post("/api/manual")
    def manual():
        data = request.get_json(force=True)
        return jsonify(controller.manual(float(data["pan"]), float(data["tilt"])))

    @app.post("/api/center")
    def center():
        return jsonify(controller.center())

    @app.post("/api/release")
    def release():
        return jsonify(controller.release())

    return app

def main():
    create_app().run(
        host=os.getenv("SNAP_GO_HOST", "0.0.0.0"),
        port=int(os.getenv("SNAP_GO_PORT", "8080")),
        debug=False,
    )
