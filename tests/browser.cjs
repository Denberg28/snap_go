// Run: npm ci && npx playwright install chromium && node tests/browser.cjs
const {chromium}=require('playwright');
const {spawn}=require('node:child_process');
const assert=require('node:assert/strict');
const {randomBytes}=require('node:crypto');
const token=randomBytes(32).toString('hex');
const proc=spawn(process.env.PYTHON||'python3',['-m','snap_go.app','--simulate','--port','8089','--config','/tmp/snap-go-browser-config.json'],{env:{...process.env,SNAP_GO_TOKEN:token},stdio:'ignore'});
(async()=>{
 let browser;
 try{
  for(let i=0;i<50;i++){try{await fetch('http://127.0.0.1:8089');break;}catch{await new Promise(r=>setTimeout(r,100));}}
  browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_PATH?{executablePath:process.env.CHROMIUM_PATH}:{})});
  const page=await browser.newPage({viewport:{width:1280,height:1000}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:8089');await page.fill('#token',token);await page.click('#connect');
  await page.waitForFunction(()=>document.querySelector('#connection').textContent==='Connected locally');
  assert.equal(await page.isVisible('#simulation'),true);assert.equal(await page.isVisible('#placeholder'),false);
  await page.click('#enable');await page.waitForFunction(()=>document.querySelector('#armed').textContent==='ENABLED');
  const stick=await page.locator('#panStick').boundingBox();
  await page.mouse.move(stick.x+stick.width*.8,stick.y+stick.height*.5);
  await page.mouse.down();
  await page.waitForFunction(()=>Number(document.querySelector('#position').textContent.split(' / ')[0])>=1550);
  await page.mouse.up();
  await page.waitForFunction(()=>document.querySelector('#panStick').getAttribute('aria-valuenow')==='0');
  await page.click('#stop');await page.waitForFunction(()=>document.querySelector('#armed').textContent==='DISABLED');
  await page.click('#openSettings');await page.fill('[name=confidence]','0.6');await page.click('#save');await page.click('#closeSettings');
  await page.selectOption('#mode','track');await page.click('#enable');await page.waitForFunction(()=>document.querySelector('#armed').textContent==='ENABLED');
  await page.click('#openSettings');await page.locator('#faultControls summary').click();await page.click('[data-fault=target]');
  await page.waitForFunction(()=>document.querySelector('#message').textContent.includes('Target lost'));
  await page.click('[data-fault=none]');
  assert.equal(await page.textContent('#armed'),'DISABLED');
  await page.screenshot({path:'/tmp/snap-go-desktop.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.screenshot({path:'/tmp/snap-go-mobile.png',fullPage:true});
  assert.deepEqual(errors,[]);console.log('Browser flow passed: auth, manual, stop, calibration, tracking loss, mobile layout; no JS errors');
 }finally{if(browser)await browser.close();proc.kill('SIGTERM');}
})().catch(e=>{console.error(e);proc.kill('SIGTERM');process.exitCode=1;});
