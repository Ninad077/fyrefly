"""The page of the Fyrefly API window (one self-contained HTML file: no downloads, no outside links)."""

PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Fyrefly API</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 64 64%22 width=%2230%22 height=%2230%22 aria-hidden=%22true%22%3E%3Cdefs%3E%3ClinearGradient id=%22fb%22 x1=%220%22 y1=%220%22 x2=%220%22 y2=%221%22%3E%3Cstop offset=%220%22 stop-color=%22%230b3d91%22/%3E%3Cstop offset=%221%22 stop-color=%22%23071a45%22/%3E%3C/linearGradient%3E%3CradialGradient id=%22fg%22 cx=%2250%25%22 cy=%2250%25%22 r=%2250%25%22%3E%3Cstop offset=%220%22 stop-color=%22%23e0fbff%22/%3E%3Cstop offset=%22.45%22 stop-color=%22%2322d3ee%22 stop-opacity=%22.75%22/%3E%3Cstop offset=%221%22 stop-color=%22%2322d3ee%22 stop-opacity=%220%22/%3E%3C/radialGradient%3E%3C/defs%3E%3Crect width=%2264%22 height=%2264%22 rx=%2215%22 fill=%22url%28%23fb%29%22/%3E%3Ccircle cx=%2232%22 cy=%2240%22 r=%2217%22 fill=%22url%28%23fg%29%22/%3E%3Cg transform=%22translate%2832 30%29 rotate%28-18%29%22%3E%3Cellipse cx=%22-11%22 cy=%22-5%22 rx=%225%22 ry=%2213%22 transform=%22rotate%28-48 -11 -5%29%22 fill=%22%23bae6fd%22 fill-opacity=%22.55%22 stroke=%22%23e0f2fe%22 stroke-width=%221.2%22/%3E%3Cellipse cx=%2211%22 cy=%22-5%22 rx=%225%22 ry=%2213%22 transform=%22rotate%2848 11 -5%29%22 fill=%22%23bae6fd%22 fill-opacity=%22.55%22 stroke=%22%23e0f2fe%22 stroke-width=%221.2%22/%3E%3Cellipse cx=%220%22 cy=%2211%22 rx=%226%22 ry=%229.5%22 fill=%22%23e0fbff%22 stroke=%22%23fff%22 stroke-width=%221.4%22/%3E%3Cpath d=%22M-5.5 8h11M-5.8 12h11.6%22 stroke=%22%2322d3ee%22 stroke-width=%221.3%22 fill=%22none%22/%3E%3Cellipse cx=%220%22 cy=%22-2%22 rx=%226.5%22 ry=%227%22 fill=%22%230a2a66%22 stroke=%22%23e0f2fe%22 stroke-width=%221.5%22/%3E%3Ccircle cx=%220%22 cy=%22-12.5%22 r=%224.3%22 fill=%22%230a2a66%22 stroke=%22%23e0f2fe%22 stroke-width=%221.5%22/%3E%3Cpath d=%22M-1.5 -16C-4-22 -9-23 -12-21M1.5 -16C4-22 9-23 12-21%22 stroke=%22%23e0f2fe%22 stroke-width=%221.4%22 fill=%22none%22 stroke-linecap=%22round%22/%3E%3C/g%3E%3C/svg%3E">
<style>
:root{--bg:#f4f6fb;--panel:#fff;--ink:#16181d;--mute:#5b6270;--line:#d6dcea;--wash:#eef2fa;--cobalt:#0b3d91;--cyan:#0891b2;
--ok:#0f7b45;--okbg:#e4f6ec;--warn:#9a5b00;--warnbg:#fff3dc;--bad:#b3261e;--badbg:#fde8e6;--code:#f1f4fb}
@media (prefers-color-scheme:dark){:root{--bg:#0e1320;--panel:#151b2b;--ink:#e7ebf5;--mute:#98a2b8;--line:#2a3350;--wash:#1b2338;--cobalt:#6ea0ff;--cyan:#38bdf8;
--ok:#5fd394;--okbg:#10301f;--warn:#f0b254;--warnbg:#3a2a0c;--bad:#ff8a80;--badbg:#3b1613;--code:#101626}}
*{box-sizing:border-box}
html,body{height:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;display:flex;flex-direction:column}
header{display:flex;align-items:center;gap:10px;padding:7px 14px;background:var(--panel);border-bottom:1px solid var(--line)}
.logo{display:flex;align-items:center;gap:9px;font-weight:800;letter-spacing:-.3px;font-size:16px}.ttl{background:linear-gradient(180deg,#0b3d91 0%,#071a45 100%);-webkit-background-clip:text;background-clip:text;color:transparent;-webkit-text-fill-color:transparent}
@media (prefers-color-scheme:dark){.ttl{background:linear-gradient(180deg,#8db8ff 0%,#4f86e8 100%);-webkit-background-clip:text;background-clip:text}}
.logo .mark{flex:none;filter:drop-shadow(0 0 5px rgba(34,211,238,.45))}.logo b{color:var(--cobalt)}
.sp{flex:1}.hint{color:var(--mute);font-size:12px}
button{font:inherit;cursor:pointer;border-radius:6px;border:1px solid var(--line);background:var(--panel);color:var(--ink);padding:6px 12px}
button:hover{background:var(--wash)}button.primary{background:var(--cobalt);border-color:var(--cobalt);color:#fff;font-weight:600}
button.primary:hover{filter:brightness(1.12)}button:disabled{opacity:.6;cursor:wait}
button.link{border:0;background:none;color:var(--cobalt);padding:2px 6px;font-size:12px}
button.ico{padding:3px 8px;border:0;background:none;color:var(--mute)}
input,select,textarea{font:inherit;color:var(--ink);background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:7px 9px;min-width:0}
input:focus,select:focus,textarea:focus{outline:2px solid var(--cobalt);outline-offset:-1px}
.envsel{display:flex;gap:6px;align-items:center}.envsel select{max-width:200px;font-weight:600}
.shell{flex:1;display:flex;min-height:0}
aside{width:270px;border-right:1px solid var(--line);background:var(--panel);display:flex;flex-direction:column;flex:none;min-height:0}
.sidetabs{display:flex;border-bottom:1px solid var(--line)}.sidetabs button{flex:1;border:0;border-radius:0;background:none;padding:9px;color:var(--mute);border-bottom:2px solid transparent}
.sidetabs button.on{color:var(--cobalt);font-weight:600;border-bottom-color:var(--cobalt)}
.sidebody{overflow:auto;padding:8px;flex:1}.sidebody .tools{display:flex;gap:6px;margin-bottom:8px}.sidebody .tools button{flex:1;padding:5px 8px;font-size:12.5px}
.coll{margin-bottom:4px}.collh{display:flex;align-items:center;gap:4px;padding:4px 4px;border-radius:5px;cursor:pointer;font-weight:600}.collh:hover,.item:hover{background:var(--wash)}
.collh .nm{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.collh .ct{color:var(--mute);font-weight:400;font-size:12px}
.item{display:flex;align-items:center;gap:6px;padding:3px 4px 3px 18px;border-radius:5px;cursor:pointer;font-size:13px}
.item .nm{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.item.on{background:var(--wash)}
.fold{padding-left:10px;border-left:1px solid var(--line);margin-left:10px}.foldh{color:var(--mute);font-size:12px;padding:3px 2px;cursor:pointer}
.m{font-weight:700;font-size:10px;min-width:38px}.m.get{color:#0f7b45}.m.post{color:#b45309}.m.put{color:#0b3d91}.m.patch{color:#7c2d92}.m.delete{color:var(--bad)}
.hrow{display:flex;gap:6px;align-items:center;padding:4px;border-radius:5px;cursor:pointer;font-size:12.5px}.hrow:hover{background:var(--wash)}
.hrow .u{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--mute)}.st{font-size:11px;font-weight:700}.st.ok{color:var(--ok)}.st.warn{color:var(--warn)}.st.bad{color:var(--bad)}
main{flex:1;display:flex;flex-direction:column;min-width:0;overflow:auto}
.reqtabs{display:flex;gap:2px;padding:6px 12px 0;background:var(--bg);overflow-x:auto;flex:none}
.rt{display:flex;align-items:center;gap:6px;max-width:210px;padding:6px 6px 6px 10px;border:1px solid var(--line);border-bottom:0;border-radius:7px 7px 0 0;background:var(--wash);cursor:pointer;font-size:12.5px;white-space:nowrap}
.rt.on{background:var(--panel);font-weight:600}.rt .nm{overflow:hidden;text-overflow:ellipsis}.rt .dot{color:var(--cyan)}.rt button{padding:0 5px;border:0;background:none;color:var(--mute)}
.work{padding:12px 14px;display:flex;flex-direction:column;gap:12px;background:var(--panel);border-top:1px solid var(--line);flex:1}
.bar{display:flex;gap:8px}.bar select{width:110px;font-weight:700}.bar input{flex:1;font-size:15px}
.resolve{font-size:12px;color:var(--mute);margin-top:-6px;overflow-wrap:anywhere}.resolve .un{color:var(--bad);font-weight:600}.resolve .dyn{color:var(--cyan)}
.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;display:flex;flex-direction:column;min-height:0}
.tabs{display:flex;gap:2px;border-bottom:1px solid var(--line);padding:0 8px;overflow-x:auto}
.tab{border:0;background:none;border-bottom:2px solid transparent;border-radius:0;padding:9px 11px;color:var(--mute);white-space:nowrap}
.tab.on{color:var(--cobalt);border-bottom-color:var(--cobalt);font-weight:600}.tab i{font-style:normal;color:var(--cyan);margin-left:4px;font-size:12px}
.pane{padding:12px;overflow:auto}.help{color:var(--mute);font-size:12px;margin:0 0 10px}
table.kv{width:100%;border-collapse:collapse}table.kv td{padding:2px 3px;vertical-align:middle}
table.kv input[type=text],table.kv input:not([type]),table.kv input[type=password]{width:100%}
table.kv td.c{width:26px;text-align:center}table.kv td.k{width:34%}table.kv td.t{width:84px}table.kv td.x{width:30px}table.kv td.sc{width:84px;font-size:12px;color:var(--mute)}table.kv td.sc label{display:flex;gap:4px;align-items:center;justify-content:center;white-space:nowrap}
.x button{border:0;background:none;color:var(--mute);padding:2px 6px}
.radios{display:flex;flex-wrap:wrap;gap:4px 16px;margin-bottom:10px}.radios label{display:flex;gap:5px;align-items:center;cursor:pointer}
.field{display:grid;grid-template-columns:170px 1fr;gap:6px 10px;align-items:center;max-width:640px;margin-bottom:8px}
textarea.big{width:100%;min-height:150px;font:12.5px/1.5 ui-monospace,Menlo,Consolas,monospace;resize:vertical}
.badges{display:flex;gap:8px;align-items:center;padding:8px 12px;border-bottom:1px solid var(--line);flex-wrap:wrap}
.pill{padding:2px 10px;border-radius:99px;font-weight:700;font-size:12.5px;background:var(--wash);color:var(--mute)}
.pill.ok{background:var(--okbg);color:var(--ok)}.pill.warn{background:var(--warnbg);color:var(--warn)}.pill.bad{background:var(--badbg);color:var(--bad)}
.stat{color:var(--mute);font-size:12.5px}.stat b{color:var(--ink)}
pre{margin:0;font:12.5px/1.55 ui-monospace,Menlo,Consolas,monospace;white-space:pre-wrap;overflow-wrap:anywhere}
pre.block{background:var(--code);border:1px solid var(--line);border-radius:6px;padding:10px 12px}
mark{background:#ffe27a;color:#000;border-radius:2px}mark.cur{background:#ff9f43}
.s{color:#0f766e}.n{color:#b45309}.kw{color:#7c2d92}.key{color:var(--cobalt)}
@media (prefers-color-scheme:dark){.s{color:#5eead4}.n{color:#fbbf24}.kw{color:#d8a8ff}}
.rep .l{padding:2px 0}.rep .okl{color:var(--ok)}.rep .badl{color:var(--bad)}.rep .infl{color:var(--cobalt)}
.rep .head{margin:14px 0 4px;font-weight:800;letter-spacing:.06em;font-size:12px;color:var(--cobalt)}
.banner{border-radius:8px;padding:10px 14px;font-weight:700;margin-top:12px}.banner.ok{background:var(--okbg);color:var(--ok)}.banner.bad{background:var(--badbg);color:var(--bad)}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px}.chip{padding:3px 10px;border-radius:99px;font-size:12px;background:var(--wash);border:1px solid var(--line)}.chip.bad{background:var(--badbg);color:var(--bad);border-color:transparent}
.fix{margin:6px 0;padding:8px 12px;border-left:3px solid var(--cyan);background:var(--wash);border-radius:0 6px 6px 0}
.fix .try{display:flex;gap:8px;align-items:flex-start;margin-top:4px}.fix code{flex:1;font:12.5px/1.5 ui-monospace,Menlo,Consolas,monospace;background:var(--code);padding:6px 8px;border-radius:5px;overflow-wrap:anywhere}
.tree details{margin-left:16px}.tree summary{cursor:pointer;list-style:none;margin-left:-14px;padding-left:14px;position:relative}
.tree summary::before{content:"\25B8";position:absolute;left:0;color:var(--mute)}.tree details[open]>summary::before{content:"\25BE"}
.tree .leaf{margin-left:16px;display:flex;gap:8px;align-items:baseline}.tree .dim{color:var(--mute)}.tree .tov{visibility:hidden;font-size:11px;padding:0 6px}.tree .leaf:hover .tov{visibility:visible}
table.data{border-collapse:collapse;font-size:12.5px}table.data th{background:var(--wash);text-align:left;position:sticky;top:0}
table.data th,table.data td{border:1px solid var(--line);padding:4px 8px;white-space:nowrap;max-width:320px;overflow:hidden;text-overflow:ellipsis}
iframe.prev{width:100%;height:380px;border:1px solid var(--line);border-radius:6px;background:#fff}
img.prev{max-width:100%;border:1px solid var(--line);border-radius:6px}
.empty{color:var(--mute);text-align:center;padding:40px 10px}
.row{display:flex;gap:8px;align-items:center;margin-bottom:6px;flex-wrap:wrap}
.toast{position:fixed;bottom:16px;left:50%;transform:translateX(-50%);background:var(--ink);color:var(--bg);padding:7px 14px;border-radius:6px;font-size:13px;opacity:0;transition:opacity .2s;pointer-events:none;z-index:99;max-width:80vw}
.toast.on{opacity:.95}
.ov{position:fixed;inset:0;background:rgba(10,15,30,.5);display:flex;align-items:flex-start;justify-content:center;padding-top:7vh;z-index:50}
.modal{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:16px 18px;width:min(520px,92vw);max-height:84vh;overflow:auto;box-shadow:0 20px 50px rgba(0,0,0,.35)}
.modal.wide{width:min(820px,94vw)}.modal h3{margin:0 0 10px}.macts{display:flex;gap:8px;justify-content:flex-end;margin-top:14px}
.menu{position:fixed;background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:4px;box-shadow:0 8px 24px rgba(0,0,0,.25);z-index:60;min-width:150px}
.menu button{display:block;width:100%;text-align:left;border:0;background:none;padding:6px 10px}.menu button.dng{color:var(--bad)}
.runrow{display:grid;grid-template-columns:1fr 60px 70px 90px;gap:8px;padding:5px 4px;border-bottom:1px solid var(--line);font-size:13px;align-items:center}
.runrow .nm{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.note{background:var(--warnbg);color:var(--warn);padding:6px 10px;border-radius:6px;font-size:12.5px;margin:6px 0}
@media (max-width:860px){aside{display:none}}
</style></head>
<body>
<header><span class="logo"><svg class="mark" viewBox="0 0 64 64" width="30" height="30" aria-hidden="true"><defs><linearGradient id="fb" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0b3d91"/><stop offset="1" stop-color="#071a45"/></linearGradient><radialGradient id="fg" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#e0fbff"/><stop offset=".45" stop-color="#22d3ee" stop-opacity=".75"/><stop offset="1" stop-color="#22d3ee" stop-opacity="0"/></radialGradient></defs><rect width="64" height="64" rx="15" fill="url(#fb)"/><circle cx="32" cy="40" r="17" fill="url(#fg)"/><g transform="translate(32 30) rotate(-18)"><ellipse cx="-11" cy="-5" rx="5" ry="13" transform="rotate(-48 -11 -5)" fill="#bae6fd" fill-opacity=".55" stroke="#e0f2fe" stroke-width="1.2"/><ellipse cx="11" cy="-5" rx="5" ry="13" transform="rotate(48 11 -5)" fill="#bae6fd" fill-opacity=".55" stroke="#e0f2fe" stroke-width="1.2"/><ellipse cx="0" cy="11" rx="6" ry="9.5" fill="#e0fbff" stroke="#fff" stroke-width="1.4"/><path d="M-5.5 8h11M-5.8 12h11.6" stroke="#22d3ee" stroke-width="1.3" fill="none"/><ellipse cx="0" cy="-2" rx="6.5" ry="7" fill="#0a2a66" stroke="#e0f2fe" stroke-width="1.5"/><circle cx="0" cy="-12.5" r="4.3" fill="#0a2a66" stroke="#e0f2fe" stroke-width="1.5"/><path d="M-1.5 -16C-4-22 -9-23 -12-21M1.5 -16C4-22 9-23 12-21" stroke="#e0f2fe" stroke-width="1.4" fill="none" stroke-linecap="round"/></g></svg><span class="ttl">Fyrefly API</span></span>
<div class="envsel"><span class="hint">Environment</span><select id="envsel"></select><button id="envmanage" title="Add, copy, delete or export environments">Manage</button></div>
<span class="sp"></span><span class="hint" id="folderhint"></span>
<button id="imp" title="Import a Postman collection or environment, or a curl command">Import</button>
<button id="settings" title="SSL, redirects, proxy, cookies">Settings</button>
<button id="quit" title="Stop the window">Quit</button></header>
<div class="shell">
<aside><div class="sidetabs"><button id="stc" class="on">Collections</button><button id="sth">History</button></div><div class="sidebody" id="side"></div></aside>
<main>
 <div class="reqtabs" id="reqtabs"></div>
 <div class="work">
  <div class="bar"><select id="method"></select><input id="url" placeholder="Paste the web address, e.g. https://api.example.com/users  (use {{HOST}} for variables)" spellcheck="false" autocomplete="off"><button class="primary" id="send">Send</button><button id="save" title="Save this request (Ctrl+S)">Save</button></div>
  <div class="resolve" id="resolve"></div>
  <div class="card"><div class="tabs" id="tabs"></div><div class="pane" id="pane"></div></div>
  <div class="card" id="resp"></div>
 </div>
</main></div>
<div class="toast" id="toast"></div>
<script>
const TOKEN="__TOKEN__";
const PRESET=__PRESET__;
const $=(s,r=document)=>r.querySelector(s);
function h(tag,attrs,...kids){const e=document.createElement(tag);for(const k in (attrs||{})){const v=attrs[k];
 if(k==='class')e.className=v;else if(k==='value')e.value=v;else if(k==='checked')e.checked=!!v;else if(k.startsWith('on'))e.addEventListener(k.slice(2),v);
 else if(v===true)e.setAttribute(k,'');else if(v!==false&&v!=null)e.setAttribute(k,v)}
 for(const c of kids.flat(9)){if(c==null||c===false)continue;e.append(c.nodeType?c:document.createTextNode(String(c)))}return e}
const esc=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
function toast(t,ms){const e=$('#toast');e.textContent=t;e.classList.add('on');clearTimeout(toast.t);toast.t=setTimeout(()=>e.classList.remove('on'),ms||1600)}
function copy(text){const done=()=>toast('Copied');if(navigator.clipboard&&window.isSecureContext)navigator.clipboard.writeText(text).then(done,fallback);else fallback();
 function fallback(){const t=h('textarea',{value:text});document.body.append(t);t.select();try{document.execCommand('copy');done()}catch(e){toast('Select and copy by hand')}t.remove()}}
const J=o=>JSON.parse(JSON.stringify(o));
async function post(path,obj){try{const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-Fyrefly-Token':TOKEN},body:JSON.stringify(obj||{})});return await r.json()}
 catch(e){return{error:'The window lost contact with Fyrefly. Is the Python session still running?'}}}
const op=(name,data)=>post('/op',Object.assign({op:name},data||{}));

/* ---------- state ---------- */
let ST={collections:[],envs:{Globals:[]},settings:{active_env:'Globals'},history:[],folder:null,persist:false,problems:[],globals:'Globals'};
let tabs=[],cur=null,cfgTab='params',sideTab='coll',tid=0;
const blank=()=>({on:true,k:'',v:'',kind:'text',file:null});
const withBlank=a=>{a=(a||[]).map(r=>Object.assign({kind:'text',file:null},r));a.push(blank());return a};
function normS(s){const d={method:'get',url:'',params:[],headers:[],auth:{},body:{},expect:'',look_for:'',times:1,timeout:'',saves:[],verify:null,redirects:null};
 const x=Object.assign(d,J(s||{}));x.auth=Object.assign({type:'none',token:'',user:'',password:'',name:'X-API-Key',value:''},x.auth||{});
 x.body=Object.assign({type:'none',json:'',raw:'',rawType:'text/plain',rows:[]},x.body||{});
 x.params=withBlank(x.params);x.headers=withBlank(x.headers);x.body.rows=withBlank(x.body.rows);x.saves=(x.saves||[]).concat([{var:'',path:''}]);return x}
const S=()=>cur.S;
function openTab(s,meta){const t={id:++tid,S:normS(s),meta:Object.assign({collection:null,rid:null,name:'',folder:''},meta||{}),last:null,rtab:'report',dirty:false};tabs.push(t);activate(t);return t}
function activate(t){cur=t;$('#method').value=t.S.method;$('#url').value=t.S.url;drawReqTabs();redraw();drawResp();drawResolve();drawSide()}
function closeTab(t){const i=tabs.indexOf(t);tabs.splice(i,1);if(!tabs.length)openTab();else if(cur===t)activate(tabs[Math.max(0,i-1)]);else drawReqTabs()}
function touch(){if(!cur.dirty){cur.dirty=true;drawReqTabs()}drawResolve()}
function title(t){if(t.meta.name)return t.meta.name;const u=(t.S.url||'').replace(/^https?:\/\//,'').split('?')[0];return u?t.S.method.toUpperCase()+' '+u:'New request'}
function drawReqTabs(){const box=$('#reqtabs');box.replaceChildren(...tabs.map(t=>h('div',{class:'rt'+(t===cur?' on':''),title:title(t),onclick:()=>activate(t)},
 h('span',{class:'m '+t.S.method,style:'min-width:0'},t.S.method.toUpperCase()),h('span',{class:'nm'},title(t).replace(/^[A-Z]+ /,'')),t.dirty?h('span',{class:'dot'},'\u25CF'):null,
 h('button',{title:'Close',onclick:e=>{e.stopPropagation();closeTab(t)}},'\u2715'))),
 h('button',{class:'ico',title:'New request',onclick:()=>openTab()},'+ New'))}

/* ---------- environments ---------- */
const activeEnv=()=>(ST.settings.active_env in ST.envs)?ST.settings.active_env:'Globals';
function varMap(){const m={};for(const n of ['Globals',activeEnv()])for(const r of (ST.envs[n]||[]))if(r.on&&r.k.trim())m[r.k.trim()]=r.secret?'\u2022\u2022\u2022\u2022':r.v;return m}
function drawEnvSel(){const s=$('#envsel');s.replaceChildren(...Object.keys(ST.envs).map(n=>h('option',{value:n},n)));s.value=activeEnv();
 $('#folderhint').textContent=ST.persist?'Saved in '+ST.folder:'Nothing is saved to disk'}
$('#envsel').onchange=async e=>{ST.settings.active_env=e.target.value;await op('settings',{settings:{active_env:e.target.value}});drawResolve();if(cfgTab==='vars')drawPane()};
function drawResolve(){const u=S().url||'',box=$('#resolve');box.replaceChildren();if(!/\{\{/.test(u))return;const m=varMap();let last=0,out=[];
 u.replace(/\{\{\s*([A-Za-z0-9_.\-$]+)\s*\}\}/g,(all,n,i)=>{out.push(u.slice(last,i));last=i+all.length;
  if(n[0]==='$')out.push(h('span',{class:'dyn'},'\u2039new '+n.slice(1)+' each time\u203A'));else if(n in m)out.push(m[n]);else out.push(h('span',{class:'un',title:'No value yet. Add it in the Variables tab.'},all));return all});
 out.push(u.slice(last));box.append('Sends to: ',...out)}
function adopt(d){if(d.error){toast(d.error,3500);return false}if(d.state){ST=d.state;drawEnvSel();drawSide();if(cfgTab==='vars')drawPane();drawResolve()}return true}
async function refreshState(){adopt(await op('state'))}

/* ---------- request bar ---------- */
const sel=$('#method');['get','post','put','patch','delete','head','options'].forEach(m=>sel.append(h('option',{value:m},m.toUpperCase())));
sel.onchange=()=>{S().method=sel.value;touch();drawReqTabs()};
$('#url').oninput=e=>{S().url=e.target.value;touch();drawReqTabs()};

/* ---------- editable rows ---------- */
function count(rows){return rows.filter(r=>r.on&&r.k.trim()).length}
function tabsDef(){const s=S(),b=s.body.type;return[
 ['params','Params',count(s.params)],['auth','Authorization',s.auth.type!=='none'?'on':0],['headers','Headers',count(s.headers)],
 ['body','Body',b!=='none'?'on':0],['vars','Variables',count((ST.envs[activeEnv()]||[]))],['checks','Checks',(s.expect||s.look_for||s.times>1)?'on':0],
 ['extract','Save to variable',s.saves.filter(r=>r.var&&r.path).length],['conn','Settings',(s.verify!==null||s.redirects!==null)?'on':0]]}
function drawTabs(){$('#tabs').replaceChildren(...tabsDef().map(([id,label,n])=>
 h('button',{class:'tab'+(cfgTab===id?' on':''),onclick:()=>{cfgTab=id;drawTabs();drawPane()}},label,n?h('i',{},n==='on'?'\u25CF':'('+n+')'):null)))}
function kv(rows,o){o=o||{};const tb=h('tbody');const chg=()=>{if(o.change)o.change();else touch();drawTabs()};
 const mk=r=>{const isLast=()=>rows[rows.length-1]===r;
  const grow=()=>{if(isLast()&&(r.k||r.v||r.file)){const nr=blank();rows.push(nr);tb.append(mk(nr))}chg()};
  const secretIn=o.secretCol?r.secret:(o.secret&&o.secret(r));
  const tr=h('tr',{},
   h('td',{class:'c'},h('input',{type:'checkbox',checked:r.on,onchange:e=>{r.on=e.target.checked;chg()}})),
   h('td',{class:'k'},h('input',{type:'text',value:r.k,placeholder:o.kp||'Name',spellcheck:'false',oninput:e=>{r.k=e.target.value;grow()}})),
   o.files?h('td',{class:'t'},h('select',{onchange:e=>{r.kind=e.target.value;if(r.kind==='text')r.file=null;redraw()}},h('option',{value:'text'},'Text'),h('option',{value:'file'},'File'))):null,
   h('td',{},r.kind==='file'?fileCell(r,grow):h('input',{type:secretIn?'password':'text',value:r.v,placeholder:(o.secretCol&&r.has&&r.keep)?'\u2022\u2022\u2022\u2022 saved (type to replace)':(o.vp||'Value'),spellcheck:'false',autocomplete:'off',
     oninput:e=>{r.v=e.target.value;r.keep=false;grow()}})),
   o.secretCol?h('td',{class:'sc'},h('label',{title:'Secret values are hidden and kept out of shared files'},h('input',{type:'checkbox',checked:r.secret,onchange:e=>{r.secret=e.target.checked;redraw()}}),' secret')):null,
   h('td',{class:'x'},h('button',{title:'Remove',onclick:()=>{const i=rows.indexOf(r);if(rows.length>1)rows.splice(i,1);else{r.k=r.v='';r.file=null}
     const l=rows[rows.length-1];if(!l||l.k||l.v||l.file)rows.push(blank());chg();redraw()}},'\u2715')));
  if(o.files){const s=tr.querySelector('select');if(s)s.value=r.kind}
  return tr};
 rows.forEach(r=>tb.append(mk(r)));return h('table',{class:'kv'},tb)}
function fileCell(r,grow){const note=h('span',{class:'hint'},r.file?r.file.name:(r.fileName?'Choose '+r.fileName+' again':''));
 const inp=h('input',{type:'file',onchange:e=>{const f=e.target.files[0];if(!f){r.file=null;return}
  if(f.size>60*1024*1024){toast('That file is over 60 MB');e.target.value='';return}
  const fr=new FileReader();fr.onload=()=>{r.file={name:f.name,type:f.type||'',b64:String(fr.result).split(',')[1]||''};grow();note.textContent=f.name+' ('+Math.ceil(f.size/1024)+' KB)'};fr.readAsDataURL(f)}});
 return h('div',{class:'row',style:'margin:0'},inp,note)}
function redraw(){drawTabs();drawPane()}
const field=(label,el)=>[h('label',{},label),el];

/* ---------- config panes ---------- */
function drawPane(){const p=$('#pane'),s=S();p.replaceChildren();
 if(cfgTab==='params')p.append(h('p',{class:'help'},'Extras added to the address after a ?  Example: name page, value 2.'),kv(s.params,{kp:'Name',vp:'Value'}));
 else if(cfgTab==='headers')p.append(h('p',{class:'help'},'Extra settings the API asks for. Example: name Accept, value application/json. Values of headers named token, key, secret, password, auth or cookie are never written to saved files.'),kv(s.headers,{kp:'Header name',vp:'Value',secret:r=>/token|key|secret|password|auth|cookie/i.test(r.k)}));
 else if(cfgTab==='vars'){const env=activeEnv(),g='Globals';
  p.append(h('p',{class:'help'},'Name a value once, then type it as {{name}} in the address, headers, auth or body. Built in: {{$guid}}, {{$timestamp}}, {{$isoTimestamp}}, {{$randomInt}}. Values marked secret are hidden, and stored apart from the shared files.'));
  const save=name=>{clearTimeout(save[name]);save[name]=setTimeout(async()=>{const d=await op('env_save',{name,rows:ST.envs[name]});
    if(d.error)toast(d.error,3000);else{ST.envs[name].forEach(r=>{if(r.secret&&r.v!==''){r.has=true;r.keep=true;r.v=''}});}},500)};
  const ensure=n=>{const a=ST.envs[n];if(!a.length||a[a.length-1].k||a[a.length-1].v)a.push({on:true,k:'',v:'',secret:false,has:false,keep:false});return a};
  p.append(h('h4',{class:'hint'},'Environment: '+env+(env===g?'':'  (on top of Globals)')),kv(ensure(env),{kp:'Variable name',vp:'Value',secretCol:true,change:()=>{save(env);drawTabs();drawResolve()}}));
  if(env!==g)p.append(h('h4',{class:'hint',style:'margin-top:16px'},'Globals  (always on)'),kv(ensure(g),{kp:'Variable name',vp:'Value',secretCol:true,change:()=>{save(g);drawTabs();drawResolve()}}))}
 else if(cfgTab==='auth'){const a=s.auth;const t=h('select',{onchange:e=>{a.type=e.target.value;touch();redraw()}},
   ...[['none','No login'],['bearer','Bearer token'],['basic','Username and password'],['header','Token or key in a header']].map(([v,l])=>h('option',{value:v},l)));t.value=a.type;
  const show=h('label',{class:'hint'},h('input',{type:'checkbox',onchange:e=>p.querySelectorAll('input[data-s]').forEach(i=>i.type=e.target.checked?'text':'password')}),' show what I type');
  const sec=(k,ph)=>h('input',{type:'password','data-s':1,value:a[k],placeholder:ph,autocomplete:'off',spellcheck:'false',oninput:e=>{a[k]=e.target.value;touch();drawTabs()}});
  const txt=(k,ph)=>h('input',{type:'text',value:a[k],placeholder:ph,spellcheck:'false',oninput:e=>{a[k]=e.target.value;touch()}});
  p.append(h('p',{class:'help'},'Only fill this in if the API asks for a login. Best practice: type {{TOKEN}} here and keep the real token in the Variables tab as a secret. Typed-in values are not saved to files.'),h('div',{class:'field'},...field('Type',t)));
  if(a.type==='bearer')p.append(h('div',{class:'field'},...field('Token',sec('token','paste your token or {{TOKEN}}'))),show,h('p',{class:'help'},'Sent as  Authorization: Bearer YOUR_TOKEN'));
  if(a.type==='basic')p.append(h('div',{class:'field'},...field('Username',txt('user','username')),...field('Password',sec('password','password or {{PASSWORD}}'))),show);
  if(a.type==='header')p.append(h('div',{class:'field'},...field('Header name',txt('name','token  or  X-API-Key')),...field('Value',sec('value','paste the value or {{TOKEN}}'))),show,h('p',{class:'help'},'Use this when the API wants the token in its own header, such as one named  token.'))}
 else if(cfgTab==='body'){const b=s.body;const types=[['none','none'],['form','form-data'],['urlencoded','x-www-form-urlencoded'],['json','JSON'],['raw','Text / XML']];
  p.append(h('div',{class:'radios'},...types.map(([v,l])=>h('label',{},h('input',{type:'radio',name:'bt',checked:b.type===v,onchange:()=>{b.type=v;touch();redraw()}}),l))));
  if(b.type==='none')p.append(h('p',{class:'help'},'This request sends no body. Choose JSON for most modern APIs, or form-data when you need to upload a file.'));
  if(b.type==='json')p.append(h('p',{class:'help'},'Type the data as JSON. You can use {{variables}}.'),h('textarea',{class:'big',spellcheck:'false',placeholder:'{\n  "name": "Asha",\n  "age": 30\n}',value:b.json,oninput:e=>{b.json=e.target.value;touch();drawTabs()}}),
   h('div',{class:'row',style:'margin-top:6px'},h('button',{class:'link',onclick:()=>{try{b.json=JSON.stringify(JSON.parse(b.json.replace(/\{\{[^}]*\}\}/g,m=>'"'+m+'"')),null,2).replace(/"(\{\{[^}]*\}\})"/g,'$1');redraw();touch()}catch(e){toast('Cannot tidy: that is not valid JSON yet')}}},'Tidy JSON')));
  if(b.type==='raw'){const t=h('select',{onchange:e=>{b.rawType=e.target.value;touch()}},...['text/plain','application/xml','text/xml','text/html','application/json'].map(v=>h('option',{value:v},v)));t.value=b.rawType;
   p.append(h('div',{class:'row'},'Content type',t),h('textarea',{class:'big',spellcheck:'false',value:b.raw,oninput:e=>{b.raw=e.target.value;touch();drawTabs()}}))}
  if(b.type==='urlencoded')p.append(h('p',{class:'help'},'A plain web form: one row per field.'),kv(b.rows,{kp:'Field name',vp:'Value'}));
  if(b.type==='form')p.append(h('p',{class:'help'},'Multipart form. Set a row to File to upload a file from your computer. Files are never saved with the request: choose them again when you reopen it.'),kv(b.rows,{kp:'Field name',vp:'Value',files:true}))}
 else if(cfgTab==='checks'){const num=(k,ph,w)=>h('input',{type:'text',value:s[k]||'',placeholder:ph,style:'width:'+w,oninput:e=>{s[k]=e.target.value;touch();drawTabs()}});
  p.append(h('p',{class:'help'},'Optional. The report says whether these were met.'),
   h('div',{class:'field'},...field('Status I expect',num('expect','200  (or 2xx)','140px')),...field('Field I expect',num('look_for','name, data.id','100%')),
    ...field('Test speed, this many times',num('times','1','80px')),...field('Wait at most (seconds)',num('timeout','default','80px'))))}
 else if(cfgTab==='extract'){const rows=s.saves;
  p.append(h('p',{class:'help'},'After the answer arrives, copy a value from it into a variable, so the next request can use {{NAME}}. Example: variable TOKEN, from data.token. You can also click "to var" next to any value in the Preview tab. Other sources: header:Name, status, body.'));
  const tb=h('tbody');const mk=r=>{const last=()=>rows[rows.length-1]===r;const grow=()=>{if(last()&&(r.var||r.path)){const n={var:'',path:''};rows.push(n);tb.append(mk(n))}touch();drawTabs()};
   return h('tr',{},h('td',{class:'k'},h('input',{type:'text',value:r.var,placeholder:'Variable name',spellcheck:'false',oninput:e=>{r.var=e.target.value;grow()}})),
    h('td',{},h('input',{type:'text',value:r.path,placeholder:'data.token   or   header:Location',spellcheck:'false',oninput:e=>{r.path=e.target.value;grow()}})),
    h('td',{class:'x'},h('button',{onclick:()=>{const i=rows.indexOf(r);rows.splice(i,1);if(!rows.length||rows[rows.length-1].var||rows[rows.length-1].path)rows.push({var:'',path:''});touch();redraw()}},'\u2715')))};
  rows.forEach(r=>tb.append(mk(r)));p.append(h('table',{class:'kv'},tb),h('p',{class:'help',style:'margin-top:8px'},'Saved into the active environment ('+activeEnv()+'). Names that look like secrets (token, key, password) are stored as secrets.'))}
 else if(cfgTab==='conn'){const tri=(k)=>{const t=h('select',{onchange:e=>{s[k]=e.target.value===''?null:e.target.value==='1';touch();drawTabs()}},h('option',{value:''},'Use the global setting'),h('option',{value:'1'},'Yes'),h('option',{value:'0'},'No'));t.value=s[k]===null?'':(s[k]?'1':'0');return t};
  p.append(h('p',{class:'help'},'Only for this request. Global defaults are in Settings (top right).'),h('div',{class:'field'},...field('Check SSL certificate',tri('verify')),...field('Follow redirects',tri('redirects'))),
   s.verify===false?h('div',{class:'note'},'SSL checking is off for this request. Only do this for servers you trust, such as an internal test server.'):null)}}

/* ---------- sending ---------- */
function payload(extra){return Object.assign({},J(S()),{env:activeEnv()},extra||{})}
async function send(){const btn=$('#send');if(btn.disabled)return;const t=cur;btn.disabled=true;btn.textContent='Sending\u2026';
 const d=await post('/send',payload());t.last=d;btn.disabled=false;btn.textContent='Send';
 if(d.error)t.rtab='report';
 if(cur===t)drawResp();
 if(d.status&&ST.persist)refreshHistory();
 if(d.saved&&d.saved.some(x=>!x.error))refreshState()}
async function refreshHistory(){const d=await op('state');if(d.state){ST.history=d.state.history;if(sideTab==='hist')drawSide()}}
$('#send').onclick=send;
document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key==='Enter'){e.preventDefault();send()}
 else if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='s'){e.preventDefault();saveCur()}else if(e.key==='Escape'){const o=$('.ov');if(o)o.remove();const m=$('.menu');if(m)m.remove()}});
$('#quit').onclick=async()=>{await post('/quit');document.body.innerHTML='<div class="empty" style="margin:auto"><h2>Closed</h2>You can close this tab. Run api.gui() again to reopen.</div>'};

/* ---------- dialogs ---------- */
function modal(titleText,body,actions,wide){const close=()=>ov.remove();const ov=h('div',{class:'ov',onclick:e=>{if(e.target===ov)close()}});
 const box=h('div',{class:'modal'+(wide?' wide':'')},h('h3',{},titleText),body,h('div',{class:'macts'},...(actions||[{label:'Close'}]).map(a=>h('button',{class:a.primary?'primary':'',onclick:async()=>{if(a.fn){const r=await a.fn(close);if(r===false)return}if(!a.keep)close()}},a.label))));
 ov.append(box);document.body.append(ov);const f=box.querySelector('input[type=text],textarea');if(f)f.focus();return close}
function ask(titleText,label,def,okLabel){return new Promise(res=>{const inp=h('input',{type:'text',value:def||'',style:'width:100%',spellcheck:'false'});let done=false;
 const fin=v=>{if(!done){done=true;res(v)}};
 const close=modal(titleText,h('div',{},h('label',{class:'hint'},label),inp),[{label:'Cancel',fn:()=>{fin(null)}},{label:okLabel||'OK',primary:true,fn:()=>{const v=inp.value.trim();if(!v){toast('Type a name first');return false}fin(v)}}]);
 inp.addEventListener('keydown',e=>{if(e.key==='Enter'){const v=inp.value.trim();if(v){fin(v);close()}}});inp.select()})}
function confirmBox(msg,okLabel){return new Promise(res=>{let done=false;const fin=v=>{if(!done){done=true;res(v)}};modal('Are you sure?',h('p',{},msg),[{label:'Cancel',fn:()=>{fin(false)}},{label:okLabel||'Delete',primary:true,fn:()=>{fin(true)}}])})}
function menu(anchor,items){const old=$('.menu');if(old)old.remove();const r=anchor.getBoundingClientRect();
 const m=h('div',{class:'menu',style:`left:${Math.min(r.left,innerWidth-170)}px;top:${r.bottom+2}px`},...items.map(([l,f,dng])=>h('button',{class:dng?'dng':'',onclick:()=>{m.remove();f()}},l)));
 document.body.append(m);setTimeout(()=>document.addEventListener('click',()=>m.remove(),{once:true}),0)}

/* ---------- save ---------- */
async function saveCur(){const t=cur;
 const doSave=async(collection,name,folder)=>{const d=await op('req_save',{collection,rid:t.meta.collection===collection?t.meta.rid:null,name,folder,req:payload()});
  if(!adopt(d))return false;t.meta={collection,rid:d.rid,name,folder};t.dirty=false;drawReqTabs();
  toast(d.stripped?'Saved. '+d.stripped+' secret value(s) were left out of the file. Use {{variables}} for tokens.':'Saved to '+collection,d.stripped?5000:1600);return true};
 if(t.meta.rid&&t.meta.collection){await doSave(t.meta.collection,t.meta.name,t.meta.folder);return}
 const names=ST.collections.map(c=>c.name);const nameIn=h('input',{type:'text',value:defaultName(t),style:'width:100%'});
 const colSel=h('select',{style:'width:100%'},...names.map(n=>h('option',{value:n},n)),h('option',{value:'__new'},'+ New collection'));
 const newIn=h('input',{type:'text',placeholder:'New collection name',style:'width:100%;display:'+(names.length?'none':'block')});
 if(!names.length)colSel.value='__new';colSel.onchange=()=>{newIn.style.display=colSel.value==='__new'?'block':'none'};
 const folderIn=h('input',{type:'text',placeholder:'optional, e.g. Auth/Login',style:'width:100%'});
 modal('Save request',h('div',{class:'field',style:'grid-template-columns:110px 1fr'},...field('Name',nameIn),...field('Collection',h('div',{},colSel,newIn)),...field('Folder',folderIn)),
  [{label:'Cancel'},{label:'Save',primary:true,fn:async()=>{const col=colSel.value==='__new'?newIn.value.trim():colSel.value;if(!col||!nameIn.value.trim()){toast('Choose a collection and a name');return false}
   if(!(await doSave(col,nameIn.value.trim(),folderIn.value.trim())))return false}}])}
function defaultName(t){const u=(t.S.url||'').split('?')[0].replace(/\/+$/,'');const tail=u.split('/').pop();return (t.S.method.toUpperCase()+' '+((tail&&!tail.startsWith('{{'))?tail:(u.replace(/^https?:\/\//,'')||'request'))).slice(0,80)}
$('#save').onclick=saveCur;

/* ---------- sidebar ---------- */
$('#stc').onclick=()=>{sideTab='coll';drawSide()};$('#sth').onclick=()=>{sideTab='hist';drawSide()};
const openFolders=new Set(),closedColl=new Set();
function openSaved(c,e){const ex=tabs.find(t=>t.meta.collection===c.name&&t.meta.rid===e.id);if(ex){activate(ex);return}openTab(e.req,{collection:c.name,rid:e.id,name:e.name,folder:e.folder})}
function drawSide(){$('#stc').className=sideTab==='coll'?'on':'';$('#sth').className=sideTab==='hist'?'on':'';const box=$('#side');box.replaceChildren();
 if(ST.problems&&ST.problems.length)box.append(...ST.problems.map(p=>h('div',{class:'note'},p)));
 if(sideTab==='coll'){box.append(h('div',{class:'tools'},h('button',{onclick:async()=>{const n=await ask('New collection','Name','','Create');if(n)adopt(await op('coll_new',{name:n}))}},'+ Collection'),h('button',{onclick:()=>importDialog()},'Import')));
  if(!ST.collections.length)box.append(h('div',{class:'hint',style:'padding:8px'},'No saved requests yet. Build one and press Save, or Import a Postman collection or a curl command.'));
  for(const c of ST.collections){const open=!closedColl.has(c.name);
   box.append(h('div',{class:'coll'},h('div',{class:'collh',onclick:()=>{open?closedColl.add(c.name):closedColl.delete(c.name);drawSide()}},h('span',{},open?'\u25BE':'\u25B8'),h('span',{class:'nm',title:c.name},c.name),h('span',{class:'ct'},c.requests.length),
     h('button',{class:'ico',title:'Run every request in order',onclick:e=>{e.stopPropagation();runDialog(c)}},'\u25B6'),
     h('button',{class:'ico',title:'More',onclick:e=>{e.stopPropagation();menu(e.target,[['Run all',()=>runDialog(c)],['Rename',async()=>{const n=await ask('Rename collection','New name',c.name,'Rename');if(n)adopt(await op('coll_rename',{name:c.name,new_name:n}))}],
      ['Export as Postman JSON',()=>exportData('export_coll',c.name,c.name+'.postman_collection.json')],['Delete',async()=>{if(await confirmBox('Delete the collection "'+c.name+'" and its '+c.requests.length+' request(s)?'))adopt(await op('coll_delete',{name:c.name}))},true]])}},'\u22EF')),
     open?collTree(c):null))}}
 else{box.append(h('div',{class:'tools'},h('button',{onclick:async()=>{if(await confirmBox('Clear the history?','Clear')){adopt(await op('history_clear'))}}},'Clear history')));
  if(!ST.history.length)box.append(h('div',{class:'hint',style:'padding:8px'},'Requests you send appear here'+(ST.persist?'. Tokens and passwords are not kept.':'.')));
  for(const x of ST.history){const r=x.req||{};box.append(h('div',{class:'hrow',title:r.url,onclick:()=>openTab(r)},h('span',{class:'m '+r.method},(r.method||'get').toUpperCase()),h('span',{class:'u'},(r.url||'').replace(/^https?:\/\//,'')),h('span',{class:'st '+(x.status<300?'ok':x.status<400?'warn':'bad')},x.status)))}}}
function collTree(c){const root={reqs:[],kids:{}};for(const e of c.requests){let n=root;for(const p of (e.folder||'').split('/').filter(Boolean)){n=n.kids[p]=n.kids[p]||{reqs:[],kids:{}}}n.reqs.push(e)}
 const draw=(n,path)=>h('div',{},...Object.keys(n.kids).map(k=>{const key=c.name+'/'+path+k;const open=!openFolders.has('x'+key);return h('div',{},h('div',{class:'foldh',onclick:()=>{open?openFolders.add('x'+key):openFolders.delete('x'+key);drawSide()}},(open?'\u25BE ':'\u25B8 ')+k),open?h('div',{class:'fold'},draw(n.kids[k],path+k+'/')):null)}),
  ...n.reqs.map(e=>h('div',{class:'item'+((cur.meta.collection===c.name&&cur.meta.rid===e.id)?' on':''),title:e.req.url,onclick:()=>openSaved(c,e)},h('span',{class:'m '+e.req.method},e.req.method.toUpperCase()),h('span',{class:'nm'},e.name),
   h('button',{class:'ico',onclick:ev=>{ev.stopPropagation();menu(ev.target,[['Duplicate',async()=>adopt(await op('req_duplicate',{collection:c.name,rid:e.id}))],['Delete',async()=>{if(await confirmBox('Delete "'+e.name+'"?'))adopt(await op('req_delete',{collection:c.name,rid:e.id}))},true]])}},'\u22EF'))));
 return draw(root,'')}
async function exportData(opName,name,file){const d=await op(opName,{name});if(d.error){toast(d.error,3000);return}download(new Blob([JSON.stringify(d.data,null,2)],{type:'application/json'}),file);toast('Exported '+file)}
function download(blob,name){const a=h('a',{href:URL.createObjectURL(blob),download:name});document.body.append(a);a.click();a.remove()}

/* ---------- environments, settings, import, run ---------- */
$('#envmanage').onclick=()=>{const body=h('div',{});const draw=()=>{body.replaceChildren(h('p',{class:'help'},'Switch the active environment in the top bar. Edit its variables in the Variables tab.'),
 ...Object.keys(ST.envs).map(n=>h('div',{class:'row'},h('b',{style:'flex:1'},n+(n==='Globals'?'  (always on)':'')+(n===activeEnv()?'  \u2713 active':'')),
  h('button',{onclick:()=>exportData('export_env',n,n+'.postman_environment.json')},'Export'),
  n==='Globals'?null:h('button',{onclick:async()=>{const nn=await ask('Copy environment','Name of the copy',n+' copy','Copy');if(nn){adopt(await op('env_duplicate',{name:n,new_name:nn}));draw()}}},'Copy'),
  n==='Globals'?null:h('button',{onclick:async()=>{if(await confirmBox('Delete the environment "'+n+'" and its saved secrets?')){adopt(await op('env_delete',{name:n}));draw()}}},'Delete'))),
 h('div',{class:'row',style:'margin-top:10px'},h('button',{onclick:async()=>{const nn=await ask('New environment','Name, for example UAT','','Create');if(nn){const d=await op('env_new',{name:nn});if(adopt(d)){ST.settings.active_env=nn;await op('settings',{settings:{active_env:nn}});drawEnvSel();draw()}}}},'+ New environment')))};
 draw();modal('Environments',body,[{label:'Close'}])};
$('#settings').onclick=()=>{const s=ST.settings;const v=h('input',{type:'checkbox',checked:s.verify}),r=h('input',{type:'checkbox',checked:s.redirects}),px=h('input',{type:'text',value:s.proxy||'',placeholder:'http://proxy.company.com:8080',style:'width:100%'}),to=h('input',{type:'text',value:s.timeout||'',placeholder:'30',style:'width:90px'});
 modal('Settings',h('div',{},h('div',{class:'field'},...field('Check SSL certificates',v),...field('Follow redirects',r),...field('Proxy',px),...field('Wait at most (seconds)',to)),
  h('div',{class:'note'},'Turn SSL checking off only for servers you trust, such as an internal test server. A proxy address that includes a password is saved in plain text.'),
  h('div',{class:'row'},h('button',{onclick:async()=>{await op('cookies_clear');toast('Cookies cleared')}},'Clear cookies'),h('button',{onclick:async()=>{adopt(await op('history_clear'));toast('History cleared')}},'Clear history')),
  ST.persist?h('p',{class:'hint'},'Your saved work is in: '+ST.folder+'. Collections are plain JSON files you can share. secrets.json holds secret values and is kept out of git.'):h('p',{class:'hint'},'Nothing is being saved (the window was opened with folder=False).')),
  [{label:'Cancel'},{label:'Save',primary:true,fn:async()=>{adopt(await op('settings',{settings:{verify:v.checked,redirects:r.checked,proxy:px.value.trim(),timeout:to.value.trim()}}))}}])};
function importDialog(){const ta=h('textarea',{class:'big',placeholder:'Paste here: a Postman collection (JSON), a Postman environment (JSON), or a curl command',spellcheck:'false'});
 const fi=h('input',{type:'file',accept:'.json,.txt,application/json',onchange:e=>{const f=e.target.files[0];if(f){const fr=new FileReader();fr.onload=()=>{ta.value=String(fr.result)};fr.readAsText(f)}}});
 const out=h('div',{});
 modal('Import',h('div',{},h('p',{class:'help'},'Bring over your work from Postman (File, Export) or paste a curl command copied from API documentation or your browser.'),h('div',{class:'row'},fi),ta,out),
  [{label:'Cancel'},{label:'Import',primary:true,keep:true,fn:async close=>{const d=await op('import',{text:ta.value});if(d.error){out.replaceChildren(h('div',{class:'note'},d.error));return false}adopt(d);
   const r=d.result;if(r.kind==='curl'){close();openTab(r.open[0]);toast('curl command opened in a new tab'+(r.notes.length?'. '+r.notes[0]:''),4000);return}
   out.replaceChildren(h('p',{},r.kind==='collection'?'Imported collection "'+r.collection+'": '+r.requests+' request(s)'+(r.environment?', and its variables as the environment "'+r.environment+'".':'.'):'Imported environment "'+r.environment+'": '+r.variables+' variable(s).'),...r.notes.filter(Boolean).map(n=>h('div',{class:'note'},n)));sideTab='coll';drawSide();return false}}])}
$('#imp').onclick=importDialog;
function runDialog(c){const rows=h('div',{});const stop=h('input',{type:'checkbox',checked:true});let running=false,halted=false;
 const mk=e=>{const r=h('div',{class:'runrow'},h('span',{class:'nm',title:e.req.url},e.name),h('span',{},''),h('span',{},''),h('span',{},'waiting'));r.e=e;return r};
 const els=c.requests.map(mk);rows.append(...els);const sum=h('div',{class:'hint',style:'margin-top:8px'},c.requests.length+' request(s) run in order, using the "'+activeEnv()+'" environment. Values saved from one answer are available to the next.');
 const go=async()=>{if(running)return;running=true;halted=false;let pass=0,fail=0;
  for(const r of els){const sp=r.children;sp[1].textContent=sp[2].textContent='';sp[3].textContent='waiting';sp[3].style.color=''}
  for(const r of els){if(halted)break;const sp=r.children;sp[3].textContent='running\u2026';const d=await post('/send',Object.assign({},J(r.e.req),{env:activeEnv()}));
   const ok=!d.error&&/RESULT: WORKING/.test(d.report||'');sp[1].textContent=d.status||'';sp[2].textContent=d.ms!=null?d.ms+' ms':'';
   sp[3].textContent=d.error?'ERROR':(ok?'PASS':'FAIL');sp[3].style.color=ok?'var(--ok)':'var(--bad)';sp[3].style.fontWeight='700';if(d.error)sp[0].title=d.error;
   ok?pass++:fail++;if(!ok&&stop.checked){halted=true}}
  sum.textContent=pass+' passed, '+fail+' failed'+(halted?' (stopped at the first failure)':'')+'.';running=false;refreshState();refreshHistory()};
 modal('Run: '+c.name,h('div',{},h('div',{class:'row'},h('label',{},stop,' stop at the first failure')),rows,sum),[{label:'Close'},{label:'Run',primary:true,keep:true,fn:go}],true)}

/* ---------- response ---------- */
function cls(st){return st<300?'ok':st<400?'warn':'bad'}
function size(n){return n<1024?n+' B':n<1048576?(n/1024).toFixed(1)+' KB':(n/1048576).toFixed(1)+' MB'}
function drawResp(){const t=cur,d=t.last,box=$('#resp');box.replaceChildren();
 if(!d){box.append(h('div',{class:'empty'},'Fill in the address and press ',h('b',{},'Send'),'. The answer, a plain-English report and fixes for any problem appear here.'));return}
 const badges=h('div',{class:'badges'});
 if(d.status){badges.append(h('span',{class:'pill '+cls(d.status)},d.status+' '+(d.reason||'')),h('span',{class:'stat'},'Time ',h('b',{},d.ms+' ms')),h('span',{class:'stat'},'Size ',h('b',{},size(d.size))),d.content_type?h('span',{class:'stat'},d.content_type):null)}
 else badges.append(h('span',{class:'pill bad'},'No answer'));
 const names=[['report','Report'],['body','Body'],['preview','Preview'],['table','Table'],['headers','Headers'],['request','Request']];
 if(!d.connected&&t.rtab!=='report')t.rtab='report';
 const tabsEl=h('div',{class:'tabs'},...names.filter(([id])=>d.connected||id==='report').map(([id,l])=>h('button',{class:'tab'+(t.rtab===id?' on':''),onclick:()=>{t.rtab=id;drawResp()}},l)));
 const pane=h('div',{class:'pane',style:'max-height:62vh'});box.append(badges,tabsEl,pane);
 ({report,body:bodyView,preview,table:tableView,headers:headersView,request:requestView})[t.rtab](pane,d)}
function report(p,d){if(d.error){p.append(h('div',{class:'banner bad'},d.error));return}
 if(d.saved&&d.saved.length)p.append(h('div',{class:'chips'},...d.saved.map(x=>x.error?h('span',{class:'chip bad'},x.error):h('span',{class:'chip',title:'from '+x.path},'Saved {{'+x.k+'}}'+(x.secret?' (secret)':' = '+x.value)+' to '+x.env))));
 const wrap=h('div',{class:'rep'});const lines=d.report.replace(/\s+$/,'').split('\n');
 for(const ln of lines){let m;
  if(/^\s*$/.test(ln))continue;
  if(m=ln.match(/^\s*\[(OK  |FAIL|INFO)\]\s*(.*)$/))wrap.append(h('div',{class:'l '+(m[1]==='OK  '?'okl':m[1]==='FAIL'?'badl':'infl')},(m[1]==='OK  '?'\u2714 ':m[1]==='FAIL'?'\u2718 ':'\u2139 ')+m[2]));
  else if(/^HOW TO FIX IT/.test(ln))wrap.append(h('div',{class:'head'},'HOW TO FIX IT'));
  else if(m=ln.match(/^RESULT:\s*(\w+)(.*)$/))wrap.append(h('div',{class:'banner '+(m[1]==='WORKING'?'ok':'bad')},'RESULT: '+m[1]+m[2]));
  else if(m=ln.match(/^\s{2}(\d+)\.\s(.*)$/))wrap.append(h('div',{class:'fix'},h('b',{},m[1]+'. '+m[2])));
  else if(m=ln.match(/^\s+(Where|Try|Note):\s+(.*)$/)){const f=wrap.lastChild;if(!f||!f.classList.contains('fix'))continue;
   if(m[1]==='Try')f.append(h('div',{class:'try'},h('code',{},m[2]),h('button',{class:'link',onclick:()=>copy(m[2])},'Copy')));
   else f.append(h('div',{},h('span',{class:'hint'},m[1]+': '),m[2]))}
  else wrap.append(h('div',{class:'l'},ln))}
 p.append(wrap)}
function colorJson(s){return esc(s).replace(/("(?:\\.|[^"\\])*")(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?/g,(m,str,colon,kw)=>{
 if(str)return colon?'<span class="key">'+str+'</span>'+colon:'<span class="s">'+str+'</span>';if(kw)return '<span class="kw">'+m+'</span>';return '<span class="n">'+m+'</span>'})}
function markHtml(text,term){const lo=text.toLowerCase(),q=term.toLowerCase();let i=0,out='',n=0;while(true){const j=lo.indexOf(q,i);if(j<0){out+=esc(text.slice(i));break}out+=esc(text.slice(i,j))+'<mark data-i="'+(n++)+'">'+esc(text.slice(j,j+q.length))+'</mark>';i=j+q.length}return[out,n]}
function bodyView(p,d){if(!d.body){p.append(h('div',{class:'empty'},d.kind==='image'?'This is an image. See the Preview tab.':'The answer has no body.'));return}
 const pre=h('pre',{class:'block'}),cnt=h('span',{class:'hint'});let at=0;
 const find=h('input',{type:'text',placeholder:'Find in the answer',style:'width:210px'});
 const paint=()=>{const term=find.value;if(term&&d.body.length<2000000){const[html,n]=markHtml(d.body,term);pre.innerHTML=html;cnt.textContent=n?(Math.min(at+1,n))+' of '+n:'no matches';at=Math.min(at,Math.max(n-1,0));const m=pre.querySelectorAll('mark');m.forEach((x,i)=>x.classList.toggle('cur',i===at));if(m[at])m[at].scrollIntoView({block:'center'})}
  else{cnt.textContent='';if(d.kind==='json'&&d.body.length<300000)pre.innerHTML=colorJson(d.body);else pre.textContent=d.body}};
 find.oninput=()=>{at=0;paint()};find.onkeydown=e=>{if(e.key==='Enter'){at++;const n=pre.querySelectorAll('mark').length;if(n&&at>=n)at=0;paint()}};
 p.append(h('div',{class:'row'},find,cnt,h('span',{class:'sp',style:'flex:1'}),h('button',{onclick:()=>copy(d.body)},'Copy'),h('button',{onclick:()=>dl(d)},'Download'),d.truncated?h('span',{class:'hint'},'Showing the first 5 MB'):null),pre);paint()}
async function dl(d){const r=await op('body',{rid:d.rid});if(r.error){toast(r.error,3500);return}const bin=atob(r.b64),u=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)u[i]=bin.charCodeAt(i);
 const ext={'application/json':'json','text/html':'html','text/plain':'txt','application/xml':'xml','text/xml':'xml','text/csv':'csv','application/pdf':'pdf','image/png':'png','image/jpeg':'jpg','image/gif':'gif','image/svg+xml':'svg','application/zip':'zip'}[r.content_type]||'bin';
 download(new Blob([u],{type:r.content_type||'application/octet-stream'}),'response.'+ext);toast('Downloaded response.'+ext)}
function tree(v,key,path){const label=key!=null?h('span',{class:'key'},JSON.stringify(key)+': '):null;
 if(v!==null&&typeof v==='object'){const arr=Array.isArray(v),ks=Object.keys(v);const det=h('details',{open:path.length<3},h('summary',{},label,h('span',{class:'dim'},(arr?'[':'{')+ks.length+(arr?' items]':' fields}'))));
  for(const k of ks)det.append(tree(v[k],arr?null:k,path.concat([k])));return det}
 const c=typeof v==='string'?'s':typeof v==='number'?'n':'kw';
 return h('div',{class:'leaf'},label,h('span',{class:c},JSON.stringify(v)),h('button',{class:'link tov',title:'Save this value into a variable',onclick:()=>saveLeaf(path,v)},'to var'))}
async function saveLeaf(path,v){const last=[...path].reverse().find(x=>isNaN(x))||'VALUE';const name=await ask('Save to variable','Variable name (use it as {{NAME}})',String(last).replace(/[^A-Za-z0-9_]/g,'_').toUpperCase(),'Save');if(!name)return;
 const dotted=path.join('.');const s=S();s.saves=s.saves.filter(r=>r.var&&r.var!==name&&r.path);s.saves.push({var:name,path:dotted});s.saves.push({var:'',path:''});
 const d=await op('set_var',{env:activeEnv(),k:name,v:typeof v==='string'?v:JSON.stringify(v)});if(adopt(d)){toast('Saved {{'+name+'}} to '+activeEnv()+'. It will refresh each time this request runs.',3500);touch();drawTabs()}}
function preview(p,d){if(d.kind==='json'){let v;try{v=JSON.parse(d.pretty)}catch(e){p.append(h('div',{class:'empty'},'Too large to draw as a tree. Use the Body tab.'));return}
  p.append(h('p',{class:'help'},'Point at a value and click "to var" to save it into a variable for your next request.'));const t=h('div',{class:'tree'});t.append(tree(v,null,[]));p.append(t)}
 else if(d.kind==='image')p.append(h('img',{class:'prev',src:d.image,alt:'response image'}));
 else if(d.kind==='html')p.append(h('p',{class:'help'},'Shown in a locked box: scripts do not run and nothing is fetched from the internet.'),h('iframe',{class:'prev',sandbox:'',srcdoc:d.body}));
 else p.append(h('div',{class:'empty'},d.body?'Plain text. See the Body tab.':'Nothing to preview.'))}
function tableView(p,d){const t=d.table;if(!t){p.append(h('div',{class:'empty'},'The answer is not a list of records, so there is no table.'));return}
 p.append(h('p',{class:'help'},'Showing '+t.data.length+(t.total>t.data.length?' of '+t.total:'')+' rows.'),
  h('table',{class:'data'},h('thead',{},h('tr',{},...t.columns.map(c=>h('th',{},c)))),h('tbody',{},...t.data.map(r=>h('tr',{},...r.map(c=>h('td',{title:c==null?'':String(c)},c==null?'':typeof c==='object'?JSON.stringify(c):String(c))))))))}
function headersView(p,d){if(d.redirects&&d.redirects.length)p.append(h('h4',{class:'hint'},'Redirects followed'),h('table',{class:'data'},h('tbody',{},...d.redirects.map(([s,u])=>h('tr',{},h('th',{},s),h('td',{style:'white-space:normal;max-width:none'},u))))),h('h4',{class:'hint',style:'margin-top:12px'},'Final answer headers'));
 p.append(h('table',{class:'data'},h('tbody',{},...d.headers.map(([k,v])=>h('tr',{},h('th',{},k),h('td',{style:'white-space:normal;max-width:none'},v))))))}
function requestView(p,d){p.append(h('h4',{class:'hint'},'What was sent'),h('table',{class:'data'},h('tbody',{},...d.request_headers.map(([k,v])=>h('tr',{},h('th',{},k),h('td',{style:'white-space:normal;max-width:none'},v))))));
 if(d.curl)p.append(h('div',{class:'row',style:'margin-top:14px'},h('b',{},'As curl'),h('button',{class:'link',onclick:()=>copy(d.curl)},'Copy')),h('pre',{class:'block'},d.curl),h('p',{class:'help'},'Secrets are hidden as ***. Add them yourself before running it.'));}
 

/* ---------- start ---------- */
(async()=>{const d=await op('state');if(d.state)ST=d.state;drawEnvSel();openTab(PRESET)})();
</script></body></html>
"""