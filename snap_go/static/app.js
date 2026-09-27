'use strict';
const $=id=>document.getElementById(id);
let token='', state=null, busy=false, previewBusy=false, configLoaded=false, lastFrameURL=null, lastOK=0,errorUntil=0;
const labels={pan_min:'Pan minimum (µs)',pan_max:'Pan maximum (µs)',pan_center:'Pan center (µs)',tilt_min:'Tilt minimum (µs)',tilt_max:'Tilt maximum (µs)',tilt_center:'Tilt center (µs)',pan_reverse:'Reverse pan',tilt_reverse:'Reverse tilt',gain:'Tracking gain (µs/s)',speed:'Maximum speed (µs/s)',deadband:'Center deadband (0.01–0.30)',class_id:'COCO class ID (0 = person)',confidence:'Minimum confidence (0.1–0.95)'};
function message(s){$('message').textContent=s;}
async function request(path,body){
 const response=await fetch(path,{method:body?'POST':'GET',headers:{Authorization:'Bearer '+token,...(body?{'Content-Type':'application/json'}:{})},body:body?JSON.stringify(body):undefined,signal:AbortSignal.timeout(1200)});
 const data=await response.json();if(!response.ok)throw Error(data.error||'Request failed');return data;
}
async function action(body){try{render(await request('/api/control',body));}catch(e){errorUntil=Date.now()+5000;message(e.message);}}
function render(s){
 const wasEnabled=state?.enabled;state=s;lastOK=Date.now();if(s.enabled&&!wasEnabled){for(const axis of ['pan','tilt']){$(axis).value=s[axis];$(axis+'Value').textContent=s[axis]+' µs';}}$('edition').textContent=s.simulate?'SIMULATION · NO HARDWARE':'HARDWARE';$('version').textContent=s.version;
 $('armed').textContent=s.enabled?'ENABLED':'DISABLED';$('armed').className='pill '+(s.enabled?'ok':'');$('enable').disabled=!s.link_ok||s.enabled;$('mode').disabled=s.enabled;$('save').disabled=s.enabled;
 $('serialStatus').textContent=s.link_ok?'● ESP32 acknowledged':'● ESP32 offline';$('serialStatus').className=s.link_ok?'ok':'bad';$('cameraStatus').textContent=s.camera_ok?'● Camera fresh':'● Camera unavailable';$('cameraStatus').className=s.camera_ok?'ok':'bad';$('fps').textContent=s.fps+' inference FPS';$('position').textContent=s.pan+' / '+s.tilt+' µs';if(Date.now()>errorUntil)message(s.reason);
 $('diagnostic').textContent=[s.serial_error,s.vision_error].filter(Boolean).join(' · ')||'Frames stay on your Pi. No recording.';$('faultControls').hidden=!s.simulate;
 for(const axis of ['pan','tilt']){$(axis).disabled=!s.enabled||s.mode!=='manual';$(axis).min=s.config[axis+'_min'];$(axis).max=s.config[axis+'_max'];}
 $('center').disabled=!s.enabled||s.mode!=='manual';
 if(!configLoaded){$('fields').replaceChildren();for(const [key,value] of Object.entries(s.config)){const label=document.createElement('label');label.textContent=labels[key]||key;const input=document.createElement('input');input.name=key;input.type=typeof value==='boolean'?'checkbox':'number';input.step='any';if(input.type==='checkbox')input.checked=value;else input.value=value;label.append(input);$('fields').append(label);}configLoaded=true;}
 for(const input of $('settings').elements)input.disabled=s.enabled;
 $('simulation').hidden=!s.simulate;$('placeholder').hidden=s.simulate||s.camera_ok;
 if(s.simulate){$('camera').hidden=true;const ctx=$('simulation').getContext('2d');ctx.fillStyle='#0c1922';ctx.fillRect(0,0,640,480);ctx.strokeStyle='#213641';for(let x=0;x<640;x+=40){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,480);ctx.stroke();}for(let y=0;y<480;y+=40){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(640,y);ctx.stroke();}ctx.fillStyle='#8fa9b9';ctx.font='16px sans-serif';ctx.fillText('SIMULATED DETECTION',20,32);if(s.target){const x=s.target.x*640,y=s.target.y*480;ctx.strokeStyle='#67dfbc';ctx.lineWidth=2;ctx.strokeRect(x-45,y-60,90,120);ctx.fillStyle='#67dfbc';ctx.fillText('subject · 95%',x-45,y-70);}}
}
$('connect').onclick=()=>{token=$('token').value.trim();configLoaded=false;poll();};
$('enable').onclick=()=>action({action:'enable',mode:$('mode').value});$('stop').onclick=()=>action({action:'stop'});
for(const axis of ['pan','tilt']){$(axis).oninput=()=>{$(axis+'Value').textContent=$(axis).value+' µs';};$(axis).onchange=()=>action({action:'move',pan:Number($('pan').value),tilt:Number($('tilt').value)});}
$('center').onclick=()=>{if(state){for(const axis of ['pan','tilt']){$(axis).value=state.config[axis+'_center'];$(axis+'Value').textContent=$(axis).value+' µs';}action({action:'move',pan:Number($('pan').value),tilt:Number($('tilt').value)});}};
$('save').onclick=()=>{const config={};for(const input of $('settings').elements)config[input.name]=input.type==='checkbox'?input.checked:Number(input.value);action({action:'config',config});};
$('settings').onsubmit=e=>e.preventDefault();document.querySelectorAll('[data-fault]').forEach(b=>b.onclick=()=>action({action:'simulate',fault:b.dataset.fault}));
async function poll(){if(!token||busy||document.hidden)return;busy=true;try{const s=await request('/api/status');render(s);if(s.enabled)await request('/api/control',{action:'lease'});$('connection').textContent='Connected locally';}catch(e){$('enable').disabled=true;$('connection').textContent='Connection lost';message(e.message+' — mount will hold when lease expires');}finally{busy=false;}}
async function preview(){if(!state||state.simulate||!state.camera_ok||previewBusy||document.hidden)return;previewBusy=true;try{const r=await fetch('/api/frame',{headers:{Authorization:'Bearer '+token},signal:AbortSignal.timeout(1200)});if(!r.ok)throw Error('No fresh video');const url=URL.createObjectURL(await r.blob());$('camera').src=url;$('camera').hidden=false;if(lastFrameURL)URL.revokeObjectURL(lastFrameURL);lastFrameURL=url;}catch(e){$('camera').hidden=true;$('placeholder').hidden=false;}finally{previewBusy=false;}}
document.addEventListener('visibilitychange',()=>{if(document.hidden&&state?.enabled)action({action:'stop'});});
setInterval(poll,250);setInterval(preview,500);setInterval(()=>{if(lastOK&&Date.now()-lastOK>1500){$('enable').disabled=true;$('armed').textContent='CONNECTION LOST';}},500);
