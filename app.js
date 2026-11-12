function toggleSidebar(){const s=document.getElementById('sidebar'),shade=document.getElementById('mobileShade');if(s)s.classList.toggle('open');if(shade)shade.classList.toggle('show')}
function toggleMessageDestination(){const d=document.getElementById('destination'),r=document.getElementById('recipient-select');if(d&&r)r.style.display=d.value==='user'?'grid':'none'}
function toggleVoiceField(){const k=document.getElementById('messageKind'),v=document.getElementById('voice-field'),t=document.getElementById('message-text');if(k&&v&&t){v.style.display=k.value==='voice'?'grid':'none';t.style.display=k.value==='text'?'grid':'none'}}
document.addEventListener('DOMContentLoaded',()=>{toggleMessageDestination();toggleVoiceField();document.querySelectorAll('.flash').forEach(el=>{setTimeout(()=>{el.style.opacity='0';el.style.transition='opacity .5s'},7500)});});


// د Word/Excel محلي ادیتور؛ د فایلونو خوندي ښکته کول د سرور له لارې هم شته.
const $ = id => document.getElementById(id);
function escapeHtml(s){return String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function toast(msg){const el=document.querySelector('.flash-stack')||document.body;const n=document.createElement('div');n.className='flash success';n.textContent=msg;el.prepend(n);setTimeout(()=>n.remove(),3200)}
function dlBlob(b,n){const u=URL.createObjectURL(b),a=document.createElement('a');a.href=u;a.download=n;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),2000)}
let offReady=false;
function offTab(k){$('offX').style.display=k==='x'?'':'none';$('offW').style.display=k==='w'?'':'none';$('otx').className='btn '+(k==='x'?'primary':'secondary');$('otw').className='btn '+(k==='w'?'primary':'secondary')}
function offInit(){if(offReady||!$('xgrid'))return;offReady=true;offTab(window.OFFICE_APP==='word'?'w':'x');xBuild();$('wdoc').dir=(window.AGENCY_LANGUAGE==='en')?'ltr':'rtl';$('wdoc').addEventListener('keydown',e=>{if(e.key==='Tab'){e.preventDefault();document.execCommand('insertText',false,'    ')}});$('wimg').addEventListener('change',e=>{const f=e.target.files[0];if(!f)return;const r=new FileReader();r.onload=()=>{$('wdoc').focus();document.execCommand('insertImage',false,r.result)};r.readAsDataURL(f);e.target.value=''})}
function wc(c,v){$('wdoc').focus();document.execCommand(c,false,v||null)}
function wSize(px){$('wdoc').focus();document.execCommand('fontSize',false,'7');$('wdoc').querySelectorAll('font[size="7"]').forEach(f=>{f.removeAttribute('size');f.style.fontSize=px+'px'})}
function wTable(){const r=+prompt('د قطارونو شمېر','3'),c=+prompt('د ستونونو شمېر','3');if(!r||!c||r>30||c>15)return;let h='<table>';for(let i=0;i<r;i++){h+='<tr>';for(let j=0;j<c;j++)h+='<td>&nbsp;</td>';h+='</tr>'}wc('insertHTML',h+'</table><p></p>')}
function wLink(){const u=prompt('لینک URL','https://');if(u&&/^https?:\/\//i.test(u))wc('createLink',u)}
function wDir(){const d=$('wdoc');d.dir=d.dir==='rtl'?'ltr':'rtl'}
function wHTML(){const n=($('wfile').value||'document');return `<html><head><meta charset="utf-8"><title>${escapeHtml(n)}</title><style>body{font-family:Tahoma}table{border-collapse:collapse}td{border:1px solid #999;padding:4px 8px}</style></head><body dir="${$('wdoc').dir}">${$('wdoc').innerHTML}</body></html>`}
function wSave(){dlBlob(new Blob(['\ufeff',wHTML()],{type:'application/msword'}),($('wfile').value||'document')+'.doc')}
function wPrint(){const f=document.createElement('iframe');f.style.cssText='position:fixed;width:0;height:0;border:0';document.body.appendChild(f);f.contentDocument.open();f.contentDocument.write(wHTML());f.contentDocument.close();setTimeout(()=>{f.contentWindow.focus();f.contentWindow.print();setTimeout(()=>f.remove(),2000)},300)}
const XS={rows:30,cols:26,v:{},st:{},a:[0,0],b:null};
const colN=c=>String.fromCharCode(65+c),xk=(r,c)=>r+','+c,fl=a=>a.flat(Infinity).filter(x=>typeof x==='number');
const XF={SUM:(...a)=>fl(a).reduce((x,y)=>x+y,0),AVERAGE:(...a)=>{const l=fl(a);return l.length?l.reduce((x,y)=>x+y,0)/l.length:'#DIV/0'},MIN:(...a)=>Math.min(...fl(a)),MAX:(...a)=>Math.max(...fl(a)),COUNT:(...a)=>fl(a).length,ROUND:(x,n=0)=>Math.round(x*10**n)/10**n,IF:(c,a,b)=>c?a:b,ABS:Math.abs,SQRT:Math.sqrt};
function cv(r,c,seen){const raw=XS.v[xk(r,c)];if(raw==null||raw==='')return '';if(raw[0]!=='='){const n=Number(String(raw).replace(/,/g,''));return String(raw).trim()!==''&&!isNaN(n)?n:raw}const k=xk(r,c);if(seen.has(k))return '#CIRC';return xEval(raw.slice(1),new Set(seen).add(k))}
function xEval(f,seen){try{let e=f.replace(/([A-Za-z])(\d+):([A-Za-z])(\d+)/g,(m,a,b,c,d)=>{const r1=+b-1,c1=a.toUpperCase().charCodeAt(0)-65,r2=+d-1,c2=c.toUpperCase().charCodeAt(0)-65,o=[];for(let r=Math.min(r1,r2);r<=Math.max(r1,r2);r++)for(let k=Math.min(c1,c2);k<=Math.max(c1,c2);k++){const x=cv(r,k,seen);o.push(typeof x==='number'?x:JSON.stringify(x))}return '['+o.join(',')+']'});e=e.replace(/\b([A-Za-z])(\d+)\b/g,(m,a,b)=>{const x=cv(+b-1,a.toUpperCase().charCodeAt(0)-65,seen);return typeof x==='number'?x:JSON.stringify(x===''?0:x)});e=e.replace(/\^/g,'**').replace(/<>/g,'!=').replace(/([^<>!=])=(?!=)/g,'$1==').replace(/\b([A-Za-z]+)\(/g,(m,n)=>n.toUpperCase()+'(');const chk=e.replace(/"(?:[^"\\]|\\.)*"/g,'""');const ok=new Set([...Object.keys(XF),'true','false']);if((chk.match(/[A-Za-z_$][\w$]*/g)||[]).some(t=>!ok.has(t))||/[;{}`\\]/.test(chk))return '#NAME?';const v=new Function(...Object.keys(XF),'return ('+e+')')(...Object.values(XF));return typeof v==='number'&&!isFinite(v)?'#DIV/0':v}catch(x){return '#ERR'}}
const fv=v=>typeof v==='number'?String(+v.toFixed(10)):String(v);
function xBuild(){let h='<tr><th class="rh"></th>'+Array.from({length:XS.cols},(_,c)=>`<th>${colN(c)}</th>`).join('')+'</tr>';for(let r=0;r<XS.rows;r++){h+=`<tr><td class="rh">${r+1}</td>`;for(let c=0;c<XS.cols;c++)h+=`<td class="xc" contenteditable="true" data-r="${r}" data-c="${c}"></td>`;h+='</tr>'}$('xgrid').innerHTML=h;xRefresh()}
function xCss(st){return (st.b?'font-weight:700;':'')+(st.i?'font-style:italic;':'')+(st.al?'text-align:'+st.al+';':'')+(st.fg?'color:'+st.fg+';':'')+(st.bg?'background:'+st.bg+';':'')}
function xInRange(r,c){const a=XS.a,b=XS.b;if(!b)return false;return r>=Math.min(a[0],b[0])&&r<=Math.max(a[0],b[0])&&c>=Math.min(a[1],b[1])&&c<=Math.max(a[1],b[1])}
function xRefresh(){const act=document.activeElement;document.querySelectorAll('#xgrid td.xc').forEach(td=>{const r=+td.dataset.r,c=+td.dataset.c;if(td!==act)td.textContent=fv(cv(r,c,new Set()));td.style.cssText=xCss(XS.st[xk(r,c)]||{});td.classList.toggle('xr',xInRange(r,c))});xInfo()}
function xInfo(){$('xname').textContent=colN(XS.a[1])+(XS.a[0]+1);const b=XS.b||XS.a,vals=[];for(let r=Math.min(XS.a[0],b[0]);r<=Math.max(XS.a[0],b[0]);r++)for(let c=Math.min(XS.a[1],b[1]);c<=Math.max(XS.a[1],b[1]);c++){const x=cv(r,c,new Set());if(typeof x==='number')vals.push(x)}$('xsum').textContent=vals.length>1?`Σ ${fv(vals.reduce((x,y)=>x+y,0))} · n=${vals.length} · x̄ ${fv(vals.reduce((x,y)=>x+y,0)/vals.length)}`:''}
document.addEventListener('focusin',e=>{const td=e.target.closest&&e.target.closest('td.xc');if(!td)return;XS.a=[+td.dataset.r,+td.dataset.c];if(!XS.shiftKeep)XS.b=null;td.textContent=XS.v[xk(XS.a[0],XS.a[1])]||'';xInfo();document.querySelectorAll('#xgrid td.xr').forEach(x=>x.classList.remove('xr'))});
document.addEventListener('focusout',e=>{const td=e.target.closest&&e.target.closest('td.xc');if(!td)return;const k=xk(+td.dataset.r,+td.dataset.c),t=td.textContent.trim();if(t==='')delete XS.v[k];else XS.v[k]=t;xRefresh()});
document.addEventListener('mousedown',e=>{const td=e.target.closest&&e.target.closest('td.xc');if(td&&e.shiftKey){e.preventDefault();XS.b=[+td.dataset.r,+td.dataset.c];xRefresh()}});
document.addEventListener('keydown',e=>{const td=e.target.closest&&e.target.closest('td.xc');if(!td)return;const r=+td.dataset.r,c=+td.dataset.c;const go=(nr,nc)=>{const n=document.querySelector(`#xgrid td[data-r="${nr}"][data-c="${nc}"]`);if(n){e.preventDefault();n.focus();const sel=getSelection(),g=document.createRange();g.selectNodeContents(n);sel.removeAllRanges();sel.addRange(g)}};if(e.key==='Enter'||e.key==='ArrowDown')go(r+1,c);else if(e.key==='ArrowUp')go(r-1,c)});
function xTargets(){const a=XS.a,b=XS.b||XS.a,o=[];for(let r=Math.min(a[0],b[0]);r<=Math.max(a[0],b[0]);r++)for(let c=Math.min(a[1],b[1]);c<=Math.max(a[1],b[1]);c++)o.push(xk(r,c));return o}
function xFmt(p,v){const T=xTargets(),on=p==='b'||p==='i'?!T.every(k=>(XS.st[k]||{})[p]):v;T.forEach(k=>{const z=XS.st[k]=XS.st[k]||{};z[p]=on});xRefresh()}
function xAuto(){const[r,c]=XS.a;let s=r;while(s>0&&typeof cv(s-1,c,new Set())==='number')s--;if(s===r)return toast('د جمع لپاره پورته شمېرې نشته.');XS.v[xk(r,c)]=`=SUM(${colN(c)}${s+1}:${colN(c)}${r})`;xRefresh()}
function xRows(){XS.rows+=10;const keep=XS.a.slice();xBuild();XS.a=keep}
function xClear(){if(!confirm('ټول جدول پاک شي؟'))return;XS.v={};XS.st={};XS.b=null;xRefresh()}
function xUsed(){let R=0,C=0;for(const k in XS.v){const[r,c]=k.split(',').map(Number);R=Math.max(R,r+1);C=Math.max(C,c+1)}return[Math.max(R,1),Math.max(C,1)]}
function xSave(kind){const[R,C]=xUsed(),n=($('xfile').value||'sheet');if(kind==='csv'){let o='';for(let r=0;r<R;r++)o+=Array.from({length:C},(_,c)=>'"'+fv(cv(r,c,new Set())).replace(/"/g,'""')+'"').join(',')+'\r\n';dlBlob(new Blob(['\ufeff',o],{type:'text/csv'}),n+'.csv');return}let h='<table border="1">';for(let r=0;r<R;r++){h+='<tr>';for(let c=0;c<C;c++)h+=`<td style="${xCss(XS.st[xk(r,c)]||{})}">${escapeHtml(fv(cv(r,c,new Set())))}</td>`;h+='</tr>'}h+='</table>';dlBlob(new Blob(['\ufeff',`<html><head><meta charset="utf-8"></head><body>${h}</body></html>`],{type:'application/vnd.ms-excel'}),n+'.xls')}
function officeServerExport(kind){const content=kind==='docx'?$('wdoc').innerText:Array.from({length:xUsed()[0]},(_,r)=>Array.from({length:xUsed()[1]},(_,c)=>String(XS.v[xk(r,c)]??'')).join('\t')).join('\n');$('serverOfficeKind').value=kind==='docx'?'docx':'xlsx';$('serverOfficeName').value=kind==='docx'?($('wfile').value||'اداري سند'):($('xfile').value||'sheet');$('serverOfficeContent').value=content;$('officeServerExport').submit()}
document.addEventListener('DOMContentLoaded',()=>{offInit();});

// د پیغام لپاره د براوزر له مایکروفون څخه مستقیم غږ ثبتول (HTTPS یا localhost اړین دی).
document.addEventListener('DOMContentLoaded',()=>{
 const start=document.getElementById('recStart'),stop=document.getElementById('recStop'),file=document.getElementById('voiceUpload'),status=document.getElementById('recStatus'),preview=document.getElementById('voicePreview');
 if(!start||!stop||!file)return;
 let recorder=null,stream=null,chunks=[];
 start.addEventListener('click',async()=>{
  try{
   if(!navigator.mediaDevices?.getUserMedia||!window.MediaRecorder)throw new Error('دا براوزر غږ ثبتول نه ملاتړ کوي.');
   stream=await navigator.mediaDevices.getUserMedia({audio:true});chunks=[];recorder=new MediaRecorder(stream);
   recorder.ondataavailable=e=>{if(e.data?.size)chunks.push(e.data)};
   recorder.onstop=()=>{const blob=new Blob(chunks,{type:recorder.mimeType||'audio/webm'});const ext=blob.type.includes('ogg')?'ogg':blob.type.includes('mp4')?'m4a':'webm';const f=new File([blob],`voice-message.${ext}`,{type:blob.type});const dt=new DataTransfer();dt.items.add(f);file.files=dt.files;preview.src=URL.createObjectURL(blob);preview.hidden=false;status.textContent='غږ ثبت شو؛ اوس پیغام لېږلای شئ.';stream?.getTracks().forEach(t=>t.stop());start.disabled=false;stop.disabled=true;};
   recorder.start();start.disabled=true;stop.disabled=false;status.textContent='غږ ثبتېږي...';
  }catch(err){status.textContent=err.message||'مایکروفون ته اجازه ورنه کړل شوه.';stream?.getTracks().forEach(t=>t.stop());}
 });
 stop.addEventListener('click',()=>{if(recorder&&recorder.state!=='inactive')recorder.stop()});
 file.addEventListener('change',()=>{if(file.files[0])status.textContent='غږیز فایل ټاکل شوی.'});
});

// د رڼا/تیاره بڼه د همدې براوزر لپاره ساتل کېږي.
function setTheme(v){const dark=v==='dark';document.documentElement.classList.toggle('dark',dark);try{localStorage.setItem('agency_theme',dark?'dark':'light')}catch(e){}const sel=document.getElementById('settingsTheme');if(sel)sel.value=dark?'dark':'light'}
document.addEventListener('DOMContentLoaded',()=>{let theme='light';try{theme=localStorage.getItem('agency_theme')||'light'}catch(e){}setTheme(theme)});


// ===== three-dot (⋮) menu =====
function toggleKebab(btn){
  const menu=btn.nextElementSibling, open=menu.classList.contains('show');
  document.querySelectorAll('.kebab-menu.show').forEach(x=>x.classList.remove('show'));
  if(open)return;
  const r=btn.getBoundingClientRect();
  menu.classList.add('show');
  const w=menu.offsetWidth||160;
  menu.style.top=Math.min(r.bottom+4,window.innerHeight-menu.offsetHeight-8)+'px';
  menu.style.left=Math.max(8,Math.min(r.left,window.innerWidth-w-8))+'px';
}
document.addEventListener('click',e=>{if(!e.target.closest('.kebab'))document.querySelectorAll('.kebab-menu.show').forEach(x=>x.classList.remove('show'))});
window.addEventListener('scroll',()=>document.querySelectorAll('.kebab-menu.show').forEach(x=>x.classList.remove('show')),true);

// ===== @mention list: every active user can be mentioned =====
(function(){
  const url=window.AGENCY_MENTION_URL; if(!url)return;
  let box=null,input=null,token=null,rows=[],sel=0,timer=null,seq=0;
  const close=()=>{if(box){box.remove();box=null}rows=[];token=null};
  const tokenAt=el=>{const pos=el.selectionStart,m=el.value.slice(0,pos).match(/(^|\s)@([^\s@]{0,30})$/);return m?{q:m[2],start:pos-m[2].length-1,end:pos}:null};
  function paint(){
    if(!box){box=document.createElement('div');box.className='mention-box';document.body.appendChild(box)}
    const r=input.getBoundingClientRect();
    box.style.left=Math.max(8,Math.min(r.left,window.innerWidth-Math.min(r.width,320)-8))+'px';box.style.top=(r.bottom+4)+'px';box.style.width=Math.min(Math.max(r.width,220),320)+'px';
    box.innerHTML='';
    rows.forEach((u,i)=>{const d=document.createElement('div');if(i===sel)d.className='on';const n=document.createElement('span');n.textContent=u.name;const sm=document.createElement('small');sm.textContent=[u.role,u.department].filter(Boolean).join(' · ');d.append(n,sm);d.addEventListener('mousedown',ev=>{ev.preventDefault();pick(u)});box.appendChild(d)});
  }
  function pick(u){
    const el=input,t=token;if(!el||!t)return;
    el.value=el.value.slice(0,t.start)+'@'+u.handle+' '+el.value.slice(t.end);
    const pos=t.start+u.handle.length+2;el.setSelectionRange(pos,pos);el.focus();
    const form=el.closest('form'),hid=form&&form.querySelector('.mention-ids');
    if(hid){const map=JSON.parse(form.dataset.mentions||'{}');map[u.id]=u.handle;form.dataset.mentions=JSON.stringify(map);hid.value=Object.keys(map).join(',')}
    close();
  }
  async function search(){
    const my=++seq;
    try{const r=await fetch(url+'?q='+encodeURIComponent(token.q),{credentials:'same-origin'});if(!r.ok)return;const d=await r.json();if(my!==seq||!token)return;rows=d.users||[];sel=0;rows.length?paint():close()}catch(e){}
  }
  document.addEventListener('input',e=>{
    const el=e.target;if(!el.classList||!el.classList.contains('mention-input'))return;
    input=el;token=tokenAt(el);if(!token){close();return}
    clearTimeout(timer);timer=setTimeout(search,120);
  });
  document.addEventListener('keydown',e=>{
    if(!box||!rows.length)return;
    if(e.key==='ArrowDown'){e.preventDefault();sel=(sel+1)%rows.length;paint()}
    else if(e.key==='ArrowUp'){e.preventDefault();sel=(sel-1+rows.length)%rows.length;paint()}
    else if(e.key==='Enter'||e.key==='Tab'){e.preventDefault();pick(rows[sel])}
    else if(e.key==='Escape'){close()}
  });
  document.addEventListener('click',e=>{if(!e.target.closest('.mention-box')&&!e.target.classList.contains('mention-input'))close()});
  document.addEventListener('submit',e=>{ // keep only mentions that are still present in the text
    const form=e.target,hid=form.querySelector&&form.querySelector('.mention-ids'),inp=form.querySelector&&form.querySelector('.mention-input');
    if(!hid||!inp)return;const map=JSON.parse(form.dataset.mentions||'{}');
    hid.value=Object.keys(map).filter(id=>inp.value.includes('@'+map[id])).join(',');
  },true);
})();

// ===== device notifications for new alerts / mentions / messages =====
(function(){
  const url=window.AGENCY_POLL_URL; if(!url)return;
  let after=null;try{const v=sessionStorage.getItem('agency_after');if(v!==null)after=+v}catch(e){}
  if('Notification' in window&&Notification.permission==='default'){
    document.addEventListener('click',()=>{try{Notification.requestPermission()}catch(e){}},{once:true});
  }
  function setBadges(n){
    document.querySelectorAll('.notification-link').forEach(a=>{let i=a.querySelector('i');if(n>0){if(!i){i=document.createElement('i');a.appendChild(i)}i.textContent=n}else if(i)i.remove()});
    document.querySelectorAll('.nav-count').forEach(i=>{if(n>0)i.textContent=n;else i.remove()});
  }
  function show(it){
    if('Notification' in window&&Notification.permission==='granted'){
      try{const nt=new Notification(it.title,{body:it.body,tag:'agency-'+it.id});nt.onclick=()=>{window.focus();location.href=it.url||window.AGENCY_NOTIF_URL}}catch(e){}
    }
    if(navigator.vibrate)try{navigator.vibrate([200,80,200])}catch(e){}
    if(typeof toast==='function')toast(it.title+(it.body?': '+it.body:''));
  }
  async function poll(){
    try{
      const r=await fetch(url+'?after='+(after===null?0:after),{credentials:'same-origin',cache:'no-store'});
      if(!r.ok)return;const d=await r.json();setBadges(d.unread);
      if(after!==null)d.items.forEach(show);
      after=d.latest;try{sessionStorage.setItem('agency_after',String(after))}catch(e){}
    }catch(e){}
  }
  poll();setInterval(poll,20000);
})();
