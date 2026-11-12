/* Django bridge for the existing agency UI. Keeps the supplied visual layout. */
(function () {
  'use strict';
  const API_URL = {
    state: '/api/state/', login: '/api/login/', logout: '/api/logout/', register: '/api/register/', resend: '/api/resend-verification/',
    doc: '/api/documents/', post: '/api/posts/', comment: '/api/posts/', mention: '/api/users/mentions/', ai: '/api/ai/ask/',
    externalNews: '/api/external-news/', officeImport: '/api/office/import/', xlsx: '/api/office/export/xlsx/', docx: '/api/office/export/docx/'
  };
  let serverMe = null, stateBusy = false, mentionTimer = null, externalTimer = null, publicVapidKey = '';
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const roleLabel = r => ({gm:'عمومي مدیر',amir:'د امریت مدیر',deputy:'مرستیال',employee:'کارکوونکی'}[String(r||'').toLowerCase()] || r || 'کارکوونکی');
  const roleCode = r => {
    const s=String(r||'').toLowerCase();
    if (['gm','عمومي مدیر','general manager'].includes(s)) return 'gm';
    if (['amir','د امریت مدیر','department manager'].includes(s)) return 'amir';
    if (['deputy','مرستیال'].includes(s)) return 'deputy';
    return 'employee';
  };
  function csrf() { const m=document.cookie.match(/(?:^|; )csrftoken=([^;]+)/); return m ? decodeURIComponent(m[1]) : ''; }
  async function api(url, opts={}) {
    const headers = new Headers(opts.headers || {});
    if (!(opts.body instanceof FormData) && !headers.has('Content-Type')) headers.set('Content-Type','application/json');
    if (opts.method && opts.method.toUpperCase() !== 'GET') headers.set('X-CSRFToken',csrf());
    const res = await fetch(url,{credentials:'same-origin',...opts,headers});
    const ct=res.headers.get('content-type')||'';
    let data;
    if (ct.includes('application/json')) data=await res.json(); else data=await res.blob();
    if(!res.ok){ const e=new Error(data && data.error ? data.error : `HTTP ${res.status}`); e.status=res.status; e.data=data; throw e; }
    return data;
  }
  function note(message){ try { if(typeof toast==='function') toast(message); else alert(message); } catch(_) { alert(message); } }
  function reportError(e){ console.error(e); note((e && e.data && e.data.error) ? `ستونزه: ${e.data.error}` : `ستونزه: ${e.message||e}`); }
  const codeUser=u=>({...u,role:roleLabel(u.role),_roleCode:roleCode(u.role),dept:u.dept||'',active:!!u.active,status:u.status||'approved'});
  function resetLocalDemo(){
    try { localStorage.removeItem('agency_session'); localStorage.removeItem('agency_ai_key'); } catch(_) {}
  }
  async function loadServerState(opts={}) {
    if(stateBusy) return;
    stateBusy=true;
    try {
      const s=await api(API_URL.state,{method:'GET'});
      serverMe=s.me;
      if(Array.isArray(s.departments) && typeof departments!=='undefined') {
        departments.splice(0,departments.length,...s.departments.map(d=>({id:d.id,name:d.name,icon:d.icon||'db',c:d.c||'#3976b9',desc:d.desc||''})));
      }
      docs=(s.docs||[]).map(d=>({...d,dept:d.dept||'',ts:+d.ts||Date.now(),attachments:d.attachments||[],can:d.can||{}}));
      news=(s.news||[]).map(p=>({id:p.id,kind:p.kind,author:p.author,role:roleCode(p.role),_roleCode:roleCode(p.role),dept:p.dept||'',text:p.text||'',ts:+p.ts||Date.now(),likes:p.likes||[],liked:!!p.liked,comments:(p.comments||[]).map(c=>({...c,role:roleCode(c.role),_roleCode:roleCode(c.role)})),media:(p.media||[]).map(a=>({...a,mid:a.id})) ,can:p.can||{}}));
      users=(s.users||[]).map(codeUser);
      notifications=(s.notifications||[]).map(n=>({...n,ts:+n.ts||Date.now(),read:!!n.read}));
      audit=(s.audit||[]).map(a=>({...a,ts:+a.ts||Date.now()}));
      messages=(s.messages||[]).map(m=>({...m,mediaId:(m.mediaUrl||'').match(/\/(\d+)\//)?.[1]||'',fromRole:roleCode(m.fromRole)}));
      const index=users.findIndex(u=>String(u.id)===String(s.me.id));
      meIdx=Math.max(0,index); me={name:s.me.name,role:roleCode(s.me.role),dept:s.me.dept||''};
      try { if(typeof syncMe==='function') syncMe(); } catch(_) { me={name:s.me.name,role:roleCode(s.me.role),dept:s.me.dept||''}; }
      if(typeof fillSelects==='function') fillSelects();
      if(typeof fillMe==='function') fillMe();
      if(typeof applyRoleUI==='function') applyRoleUI();
      if(typeof renderAll==='function') renderAll();
      const gate=document.getElementById('gate'); if(gate) gate.style.display='none';
      if(s.vapid) { publicVapidKey=s.vapid; if('Notification' in window && Notification.permission==='granted') setupPush(s.vapid).catch(console.warn); }
      if(opts.announce) note('معلومات له سرور څخه تازه شول.');
    } catch(e) {
      if(e.status===401) { const gate=document.getElementById('gate'); if(gate) gate.style.display='grid'; if(typeof gateMode==='function') gateMode(true); }
      else reportError(e);
    } finally { stateBusy=false; }
  }
  function noDemoSave(){ /* all durable data lives in Django */ }
  window.saveDemoData=noDemoSave;
  window.gateGo=async function(){
    const email=(document.getElementById('gEmail').value||'').trim().toLowerCase();
    const password=document.getElementById('gPw').value||'';
    const msg=document.getElementById('gMsg');
    if(!email||!password){msg.textContent='ایمیل او پټنوم ولیکئ.';return;}
    try {
      if(typeof gReg!=='undefined' && gReg){
        const name=(document.getElementById('gName').value||'').trim();
        const rawRole=document.getElementById('gRole').value;
        const role=roleCode(rawRole);
        if(!name || password.length<6){msg.textContent='نوم او لږ تر لږه ۶ توري پټنوم ولیکئ.';return;}
        if(role==='gm'||role==='deputy'){msg.textContent='د ثبت له لارې یوازې کارمند یا د امریت مدیر ټاکل کېدای شي.';return;}
        const result=await api(API_URL.register,{method:'POST',body:JSON.stringify({name,email,password,role,dept:document.getElementById('gDept').value})});
        if(result.verify_required){
          msg.textContent=result.mail_console ? 'حساب ثبت شو. د ایمیل تایید لینک د Django د سرور په ټرمینل کې چاپ شوی؛ له تایید وروسته د مدیر تصویب ته انتظار وباسئ.' : (result.mail_sent ? 'حساب ثبت شو. د ایمیل تایید لینک مو ایمیل ته ولېږل شو؛ له تایید وروسته د مدیر تصویب ته انتظار وباسئ.' : 'حساب ثبت شو، خو ایمیل ونه لېږل شو. د SMTP تنظیمات وګورئ.');
          const extra=document.getElementById('gVerifyAgain'); if(extra) extra.style.display='inline-block';
        } else msg.textContent='حساب ثبت شو؛ د عمومي مدیر د تصویب لپاره انتظار وکړئ.';
        window.gateMode(true); msg.textContent=result.verify_required ? (result.mail_console?'حساب ثبت شو؛ د تایید لینک د Django په ټرمینل کې چاپ شو.':(result.mail_sent?'حساب ثبت شو؛ د تایید لینک ایمیل ته ولېږل شو.':'حساب ثبت شو؛ ایمیل ونه لېږل شو، SMTP وګورئ.')) : 'حساب ثبت شو؛ د مدیر تصویب ته انتظار وکړئ.';
        return;
      }
      await api(API_URL.login,{method:'POST',body:JSON.stringify({email,password})});
      await loadServerState();
      document.getElementById('gPw').value='';
      if(typeof showPage==='function') showPage('dashboard');
    } catch(e) {
      const messages={bad_credentials:'ایمیل یا پټنوم ناسم دی.',inactive:'حساب غیرفعال دی.',unverified:'لومړی خپل ایمیل تایید کړئ.',pending:'حساب د عمومي مدیر د تصویب په تمه دی.',exists:'دا ایمیل مخکې ثبت دی.',bad_email:'ایمیل ناسم دی.',mail_failed:'ایمیل ونه لېږل شو.'};
      msg.textContent=(e.data&&messages[e.data.error])||messages[e.message]||`ننوتل/ثبت ناکام شول: ${e.data?.error||e.message}`;
    }
  };
  window.resendVerification=async function(){
    const email=(document.getElementById('gEmail').value||'').trim();
    try { const r=await api(API_URL.resend,{method:'POST',body:JSON.stringify({email})}); note(r.mail_console?'د تایید لینک د Django په ټرمینل کې چاپ شو.':'که دا ایمیل ثبت شوی او تایید ته اړتیا لري، لینک ورته ولېږل شو.'); }
    catch(e){reportError(e);}
  };
  window.logout=async function(){
    try { await api(API_URL.logout,{method:'POST',body:'{}'}); } catch(e){console.warn(e);}
    resetLocalDemo(); location.reload();
  };

  // Client-side permission hints mirror server checks; every server action independently re-checks permission.
  window.permFor=function(owner,dept){
    if(me.role==='gm') return {edit:true,del:true};
    if(owner===me.name) return {edit:true,del:true};
    if(me.role==='amir' && dept && dept===me.dept){
      const u=users.find(x=>x.name===owner); if(u && ['employee','deputy'].includes(u._roleCode)) return {edit:true,del:true};
    }
    return {edit:false,del:false};
  };
  window.can=function(){return true;};
  window.applyRoleUI=function(){
    document.querySelectorAll('.nav button').forEach(b=>{b.style.display=(['users','audit'].includes(b.dataset.page)&&me.role!=='gm')?'none':'';});
    const compose=document.getElementById('msgComposeBtn'); if(compose) compose.style.display=me.role==='employee'?'none':'';
    const ub=document.querySelector('#users .section-head .btn'); if(ub) ub.style.display=me.role==='gm'?'':'none';
    const newDoc=document.querySelector('#documents .section-head .btn'); if(newDoc) newDoc.style.display='';
  };
  window.renderFeed=function(kind){
    const box=document.getElementById('feed_'+kind); if(!box)return;
    const tools=['image','video','audio','file'].map(k=>`<button onclick="openPost('${kind}','${k}')"><span style="color:${KI[k][1]}">${svg(KI[k][0])}</span>${t('tool_'+k)}</button>`).join('');
    const list=news.filter(n=>n.kind===kind).sort((a,b)=>b.ts-a.ts);
    box.innerHTML=`<div class="composer"><div class="comp-top"><div class="avatar">${esc((me.name||'?').slice(0,1))}</div><button class="comp-input" onclick="openPost('${kind}')">${t('composer_ph')}</button></div><div class="comp-tools">${tools}</div></div>`+(list.map(postHTML).join('')||`<div class="panel empty">${t('empty_nopost')}</div>`);
    hydrate(box);
  };
  window.hydrate=async function(root){
    for(const el of (root||document).querySelectorAll('.pmi,.mpl')){
      const id=el.dataset.mid; const k=el.dataset.k||'audio';
      const target=el.classList.contains('pmi')?el.querySelector('.pm-view'):el;
      if(!id||!target)continue;
      const url=`/files/${encodeURIComponent(id)}/`;
      if(k==='image') target.innerHTML=`<img src="${url}" class="preview-media" style="background:none;margin:0">`;
      else if(k==='video') target.innerHTML=`<video src="${url}" controls class="preview-media" style="margin:0"></video>`;
      else if(k==='audio') target.innerHTML=`<audio src="${url}" controls style="width:100%"></audio>`;
      else target.innerHTML=`<a href="${url}?dl=1" class="btn light">${svg('clip')} فایل ډاونلوډ</a>`;
    }
  };
  window.dlMedia=function(mid){const a=document.createElement('a');a.href=`/files/${encodeURIComponent(mid)}/?dl=1`;a.click();};
  window.viewDoc=async function(id){const d=docs.find(x=>x.id===id);if(!d)return;document.getElementById('previewTitle').textContent=d.title;document.getElementById('previewDetails').textContent=`${d.employee||''} · ${deptName(d.dept)} · ${fmtDate(d.ts)}\n${d.description||''}`;const holder=document.getElementById('previewAttachments');holder.innerHTML='';for(const a of (d.attachments||[])){const row=document.createElement('div');row.className='attachment-item';row.innerHTML=`<div class="attachment-meta">📎 ${esc(a.name)} (${formatBytes(a.size)})</div><div class="attachment-actions"><a class="btn light" href="/files/${a.id}/" target="_blank" rel="noopener">کتل</a><a class="btn light" href="/files/${a.id}/?dl=1">ډاونلوډ</a></div>`;holder.appendChild(row);}if(!(d.attachments||[]).length)holder.innerHTML='<div class="empty">ضمیمه فایل نشته.</div>';openModal('previewModal');if(['gm','amir'].includes(me.role)&&!d.viewed){try{await api(`/api/documents/${id}/viewed/`,{method:'POST',body:'{}'});await loadServerState();}catch(e){console.warn(e);}}};
  window.likePost=async function(id){try{await api(`/api/posts/${id}/like/`,{method:'POST',body:'{}'});await loadServerState();}catch(e){reportError(e);}};
  window.toggleCm=function(id){try{openCm.has(id)?openCm.delete(id):openCm.add(id);renderNews();}catch(e){}}
  window.addComment=async function(id){
    const inp=document.getElementById('ci_'+id); const text=(inp?.value||'').trim(); if(!text)return;
    try { await api(`/api/posts/${id}/comments/`,{method:'POST',body:JSON.stringify({text})}); openCm.add(id); await loadServerState(); }
    catch(e){reportError(e);}
  };
  window.delComment=async function(pid,index){
    const p=news.find(x=>x.id===pid),c=p&&p.comments[index]; if(!c)return;
    if(!confirm('دا تبصره حذف شي؟'))return;
    try { await api(`/api/comments/${c.id}/delete/`,{method:'POST',body:'{}'}); await loadServerState(); }
    catch(e){reportError(e);}
  };
  window.mentionSuggest=function(inp){
    const box=inp.parentNode.querySelector('.mbox'); if(!box)return;
    const m=inp.value.match(/@([^\s@]*)$/); if(!m){box.style.display='none';return;}
    const q=m[1].replace(/_/g,' '); clearTimeout(mentionTimer);
    mentionTimer=setTimeout(async()=>{
      try {
        const data=await api(`${API_URL.mention}?q=${encodeURIComponent(q)}`,{method:'GET'});
        const list=data.users||[];
        box.innerHTML=list.map(u=>`<button type="button" data-name="${esc(u.name.replace(/\s+/g,'_'))}" onclick="pickMention(this,this.dataset.name)">${esc(u.name)} <small>${esc(roleLabel(u.role))}</small></button>`).join('');
        box.style.display=list.length?'block':'none';
      } catch(e){console.warn(e);box.style.display='none';}
    },160);
  };
  window.pickMention=function(btn,name){
    const wrap=btn.closest('.cm-in'),input=wrap&&wrap.querySelector('input'); if(!input)return;
    input.value=input.value.replace(/@([^\s@]*)$/,'@'+name+' '); const box=wrap.querySelector('.mbox');if(box)box.style.display='none';input.focus();
  };

  // Posts: multipart uploads and server-owned attachment removal.
  window.openPost=function(kind,pick,editId){
    postKind=kind; editingPostId=editId||null; picked=[]; renderPicked();
    const p=editId?news.find(x=>x.id===editId):null;
    document.getElementById('postText').value=p?p.text:'';
    document.getElementById('postTitle').textContent=p?'پوسټ اصلاح کول':(kind==='important'?'نوی مهم خبر':'نوی عمومي خبر');
    const dept=document.getElementById('postDept'); dept.value=p?p.dept:(me.role==='gm'?'':me.dept); dept.disabled=me.role!=='gm';
    document.getElementById('pickTools').style.display=''; document.getElementById('postPicked').style.display='';
    let holder=document.getElementById('postExistingAttachments');
    if(!holder){holder=document.createElement('div');holder.id='postExistingAttachments';holder.className='selected-files';document.getElementById('postPicked').after(holder);}
    holder.innerHTML=p?(p.media||[]).map(a=>`<label class="file-chip"><input type="checkbox" value="${a.id}" class="post-remove-file"> حذف ${esc(a.name)}</label>`).join(''):'';
    openModal('postModal'); if(pick&&!p)document.getElementById('fp_'+pick).click();
  };
  window.editPost=function(id){const p=news.find(x=>x.id===id);if(!p||!permFor(p.author,p.dept).edit){deny();return;}openPost(p.kind,null,id);};
  window.deletePost=async function(id){if(!confirm('دا پوسټ او ضمیمې حذف شي؟'))return;try{await api(`/api/posts/${id}/delete/`,{method:'POST',body:'{}'});await loadServerState();}catch(e){reportError(e);}};
  window.submitPost=async function(){
    const text=document.getElementById('postText').value.trim(); const f=new FormData();f.append('text',text);f.append('kind',postKind);f.append('dept',document.getElementById('postDept').value);
    for(const file of (picked||[])) f.append('files',file,file.name);
    const holder=document.getElementById('postExistingAttachments');
    if(editingPostId && holder) holder.querySelectorAll('.post-remove-file:checked').forEach(x=>f.append('remove',x.value));
    if(!text && !(picked||[]).length && !(editingPostId && news.find(p=>p.id===editingPostId)?.media?.length)) {note('متن یا فایل اضافه کړئ.');return;}
    try {
      if(editingPostId) await api(`/api/posts/${editingPostId}/update/`,{method:'POST',body:f});
      else await api(API_URL.post,{method:'POST',body:f});
      closeModal('postModal'); picked=[];editingPostId=null;await loadServerState();note('پوسټ خوندي شو.');
    } catch(e){reportError(e);}
  };

  window.docActions=function(d){const p=permDoc(d);return `<button class="btn light" onclick="viewDoc(${d.id})">${t('btn_view')}</button> ${['gm','amir'].includes(me.role)&&!d.viewed?`<button class="btn gold" onclick="markViewed(${d.id})">${t('btn_markviewed')}</button> `:''}${['gm','amir'].includes(me.role)?`<button class="btn light" title="${t('btn_alert')}" onclick="openAlert(${d.id})">${svg('bell')}</button> `:''}${docKebab(d,p)}`;};
  window.renderArchive=function(){const q=(document.getElementById('archiveSearch')?.value||'').toLowerCase();const list=vdocs().filter(d=>d.status==='آرشیف شوی'||(d.title+' '+d.employee).toLowerCase().includes(q));document.getElementById('archiveTable').innerHTML=tableHTML(docRows(list),t('empty_nodoc'));};

  // Documents and reports.
  function fileRemoveWidget(holderId, files, cls){
    let holder=document.getElementById(holderId); if(!holder){holder=document.createElement('div');holder.id=holderId;holder.className='selected-files';document.getElementById('docFilesWrap').appendChild(holder);}
    holder.innerHTML=(files||[]).map(a=>`<label class="file-chip"><input type="checkbox" class="${cls}" value="${a.id}"> د لرې کولو لپاره: ${esc(a.name)}</label>`).join('');
  }
  window.openDocNew=function(){editingDocId=null;document.getElementById('docForm').reset();document.getElementById('docDept').value=me.dept||departments[0]?.id||'';document.getElementById('docEmployeeInput').value=me.name;document.getElementById('docEmployeeInput').readOnly=me.role!=='gm';fileRemoveWidget('docExistingAttachments',[],'doc-remove-file');updateSelectedFiles();setDocModalMode();openModal('docModal');};
  window.editDoc=function(id){
    const d=docs.find(x=>x.id===id);if(!d||!permFor(d.employee,d.dept).edit){deny();return;}
    editingDocId=id;document.getElementById('docTitleInput').value=d.title;document.getElementById('docDept').value=d.dept;document.getElementById('docPeriod').value=d.period;document.getElementById('docEmployeeInput').value=d.employee;document.getElementById('docEmployeeInput').readOnly=me.role!=='gm';document.getElementById('docDescInput').value=d.description||'';
    fileRemoveWidget('docExistingAttachments',d.attachments,'doc-remove-file');setDocModalMode();openModal('docModal');
  };
  window.deleteDoc=async function(id){if(!confirm('دا راپور او فایلونه حذف شي؟'))return;try{await api(`/api/documents/${id}/delete/`,{method:'POST',body:'{}'});await loadServerState();}catch(e){reportError(e);}};
  window.markViewed=async function(id){try{await api(`/api/documents/${id}/viewed/`,{method:'POST',body:'{}'});await loadServerState();}catch(e){reportError(e);}};
  window.openAlert=function(id){if(!['gm','amir'].includes(me.role)){note('د خبرداري د لېږلو اجازه نه لرئ.');return;}const d=docs.find(x=>x.id===id);if(!d)return;alertDoc=d;document.getElementById('alertWho').textContent=me.role==='gm'?'ټولو کارکوونکو او امریتونو ته':'د خپل امریت کارکوونکو ته';document.getElementById('alertText').value=`د راپور په اړه: ${d.title}`;openModal('alertModal');};
  window.sendAlert=async function(){const msg=document.getElementById('alertText').value.trim();if(!msg||!alertDoc)return;try{const r=await api(`/api/documents/${alertDoc.id}/alert/`,{method:'POST',body:JSON.stringify({message:msg})});closeModal('alertModal');await loadServerState();note(`خبرتیا ${r.n||0} کسانو ته ولېږل شوه.`);}catch(e){reportError(e);}};
  const docForm=document.getElementById('docForm');
  if(docForm) docForm.addEventListener('submit',async e=>{
    e.preventDefault();e.stopImmediatePropagation();
    const f=new FormData(docForm);
    const holder=document.getElementById('docExistingAttachments');if(editingDocId&&holder)holder.querySelectorAll('.doc-remove-file:checked').forEach(x=>f.append('remove',x.value));
    if(me.role!=='gm') f.set('dept',me.dept);
    try{if(editingDocId)await api(`/api/documents/${editingDocId}/update/`,{method:'POST',body:f});else await api(API_URL.doc,{method:'POST',body:f});closeModal('docModal');await loadServerState();note('راپور په سرور کې ثبت شو.');}
    catch(e2){reportError(e2);}
  },true);

  // Role-limited alert and other staff endpoints.
  window.approveUser=async function(i){const u=users[i];if(!u||me.role!=='gm')return;try{await api(`/api/users/${u.id}/approve/`,{method:'POST',body:'{}'});await loadServerState();}catch(e){reportError(e);}};
  window.toggleUser=async function(i){const u=users[i];if(!u||me.role!=='gm')return;try{await api(`/api/users/${u.id}/toggle/`,{method:'POST',body:'{}'});await loadServerState();}catch(e){reportError(e);}};
  window.deleteUser=async function(i){const u=users[i];if(!u||me.role!=='gm'||!confirm('دا حساب حذف شي؟'))return;try{await api(`/api/users/${u.id}/delete/`,{method:'POST',body:'{}'});await loadServerState();}catch(e){reportError(e);}};
  window.toggleGM=async function(i){const u=users[i];if(!u||me.role!=='gm')return;try{await api(`/api/users/${u.id}/gm/`,{method:'POST',body:'{}'});await loadServerState();}catch(e){reportError(e);}};
  const userForm=document.getElementById('userForm');
  if(userForm)userForm.addEventListener('submit',async e=>{e.preventDefault();e.stopImmediatePropagation();if(me.role!=='gm')return;const fd=new FormData(userForm),password=String(fd.get('password')||'');if(password.length<6){note('پټنوم باید لږ تر لږه ۶ توري ولري.');return;}try{await api('/api/users/',{method:'POST',body:JSON.stringify({name:fd.get('name'),email:fd.get('email'),password,role:roleCode(fd.get('role')),dept:fd.get('dept')})});closeModal('userModal');await loadServerState();}catch(er){reportError(er);}},true);

  // Notifications and private messages.
  window.readNotification=async function(i){const n=notifications[i];if(!n)return;try{await api('/api/notifications/read/',{method:'POST',body:JSON.stringify({id:n.id})});await loadServerState();}catch(e){reportError(e);}};
  window.markAllNotifications=async function(){try{await api('/api/notifications/read/',{method:'POST',body:'{}'});await loadServerState();}catch(e){reportError(e);}};
  window.msgTargets=function(){
    if(me.role==='gm') return [{v:'all',l:'ټولو کارکوونکو ته'},...users.filter(u=>u.active&&String(u.id)!==String(users[meIdx]?.id)).map(u=>({v:'u:'+u.id,l:u.name+' — '+roleLabel(u._roleCode)}))];
    if(me.role==='amir') return [{v:'dept',l:'د خپل امریت کارکوونکو ته'},...users.filter(u=>u.active&&u.dept===me.dept&&u._roleCode!=='amir'&&u.name!==me.name).map(u=>({v:'u:'+u.id,l:u.name}))];
    return [];
  };
  window.sendMsg=async function(){
    const f=new FormData();f.append('to',document.getElementById('msgTo').value);f.append('kind',msgType||'text');
    if(msgType==='voice'){if(!recBlob){note('لومړی غږ ثبت کړئ.');return;}f.append('audio',recBlob,'voice-message.webm');}
    else f.append('text',document.getElementById('msgText').value||'');
    try{await api('/api/messages/',{method:'POST',body:f});closeModal('msgModal');await loadServerState();note('پیغام ولېږل شو.');}catch(e){reportError(e);}
  };
  window.sendMessage=window.sendMsg;
  window.deleteMsg=async function(id){if(!confirm('دا پیغام حذف شي؟'))return;try{await api(`/api/messages/${id}/delete/`,{method:'POST',body:'{}'});await loadServerState();}catch(e){reportError(e);}};
  window.msgVisible=function(){return true;};
  window.renderMessages=function(){
    const box=document.getElementById('messagesList');if(!box)return;
    box.innerHTML=messages.map(m=>{const to=m.to==='all'?'ټولو ته':m.to==='dept'?`امریت: ${esc(deptName(m.toDept))}`:esc(m.toName||'');const media=m.mediaId?`<audio controls src="/files/${m.mediaId}/" style="width:100%"></audio>`:'';return `<div class="msg"><div class="msg-top"><span><b>${esc(m.from)}</b> <span class="badge-role">${esc(roleLabel(m.fromRole))}</span> ← ${to}</span><span class="muted">${fmtDateTime(m.ts)} ${(me.role==='gm'||m.from===me.name)?`<button class="btn danger" style="padding:3px 8px" onclick="deleteMsg(${m.id})">${svg('trash')}</button>`:''}</span></div>${m.kind==='voice'?media:`<p class="post-text">${esc(m.text)}</p>`}</div>`;}).join('')||'<div class="panel empty">پیغام نشته.</div>';
  };

  // AI uses only the authenticated server endpoint and only accessible system uploads.
  window.askAI=async function(){
    const question=document.getElementById('aiQ').value.trim(),out=document.getElementById('aiOut');if(!question)return;
    out.textContent='د سیستم اسناد تحلیل کېږي…';
    try{const data=await api(API_URL.ai,{method:'POST',body:JSON.stringify({question,days:document.getElementById('aiPeriod').value||30})});out.textContent=data.answer||'ځواب ترلاسه نه شو.';}
    catch(e){out.textContent=e.data?.error==='ai_not_configured'?'د Anthropic API key په Django سرور کې نه ده تنظیم شوې.':'AI ته اړیکه ناکامه شوه: '+(e.data?.error||e.message);}
  };

  // Public external news section. RSS polling runs on the server, this is only the reader UI.
  function ensureExternalNewsUI(){
    const sidebar=document.querySelector('.sidebar .nav');
    if(sidebar&&!document.querySelector('[data-page="externalnews"]')){
      const b=document.createElement('button');b.dataset.page='externalnews';b.innerHTML='<span class="ico">◉</span><span>د افغانستان او نړۍ خبرونه</span>';b.addEventListener('click',()=>showPage('externalnews'));sidebar.appendChild(b);
    }
    const content=document.querySelector('.content');
    if(content&&!document.getElementById('externalnews')){
      const sec=document.createElement('section');sec.className='section';sec.id='externalnews';
      sec.innerHTML=`<div class="section-head"><div><h2>د افغانستان او نړۍ خبرونه</h2><p>له عامه ویب‌سایټونو او RSS سرچینو څخه راټول شوي خبرونه</p></div><button class="btn light" onclick="renderExternalNews()">تازه کول</button></div>
      <div class="filters"><select class="field" id="extCountry"><option value="all">ټول هېوادونه</option><option value="afghanistan">افغانستان</option><option value="world">نړۍ</option><option value="pakistan">پاکستان</option><option value="iran">ایران</option><option value="usa">امریکا</option></select>
      <select class="field" id="extCategory"><option value="all">ټولې موضوعګانې</option><option value="urgent">عاجل</option><option value="political">سیاسي</option><option value="security">امنیتي</option><option value="economy">اقتصادي</option><option value="technology">ټکنالوژي</option><option value="society">ټولنیز</option><option value="education">ښوونه او روزنه</option><option value="health">روغتیا</option><option value="sports">ورزش</option><option value="other">نور</option></select><input class="field search" id="extSearch" placeholder="په خبرونو کې لټون…"></div><div class="report-feed" id="externalNewsFeed"><div class="empty">خبرونه راوړل کېږي…</div></div>`;
      content.appendChild(sec);
      sec.querySelectorAll('select,input').forEach(el=>el.addEventListener('change',()=>renderExternalNews()));
      const search=document.getElementById('extSearch');search.addEventListener('input',()=>renderExternalNews());
    }
    if(typeof PAGE_KEY!=='undefined') PAGE_KEY.externalnews='nav_externalnews';
    if(typeof I18N_SRC!=='undefined') I18N_SRC.nav_externalnews=['د افغانستان او نړۍ خبرونه','خبرهای افغانستان و جهان','أخبار أفغانستان والعالم','Afghanistan & World News'];
  }
  window.renderExternalNews=async function(){
    const box=document.getElementById('externalNewsFeed');if(!box)return;
    const country=document.getElementById('extCountry')?.value||'all',category=document.getElementById('extCategory')?.value||'all',q=document.getElementById('extSearch')?.value||'';
    box.innerHTML='<div class="empty">خبرونه تازه کېږي…</div>';
    try{
      const data=await api(`${API_URL.externalNews}?country=${encodeURIComponent(country)}&category=${encodeURIComponent(category)}&q=${encodeURIComponent(q)}&limit=150`,{method:'GET'});
      const names={afghanistan:'افغانستان',world:'نړۍ',pakistan:'پاکستان',iran:'ایران',usa:'امریکا'};
      const cats={urgent:'عاجل',political:'سیاسي',security:'امنیتي',economy:'اقتصادي',technology:'ټکنالوژي',society:'ټولنیز',education:'ښوونه',health:'روغتیا',sports:'ورزش',other:'نور'};
      box.innerHTML=(data.items||[]).map(n=>`<article class="report-card"><div class="report-card-top"><div><span class="status ${n.category==='urgent'?'red':'blue'}">${esc(cats[n.category]||n.category)}</span> <span class="status">${esc(names[n.country]||n.country)}</span></div><span class="report-date">${n.ts?fmtDate(n.ts):''}</span></div><h3>${esc(n.title)}</h3><p>${esc(n.summary||'')}</p><div class="report-card-actions"><small class="muted">${esc(n.source||'RSS')}</small><a class="btn light" href="${esc(n.url)}" target="_blank" rel="noopener noreferrer">اصلي خبر پرانیزئ ↗</a></div></article>`).join('')||'<div class="panel empty">په دې فلټر کې خبر نه شته. RSS worker او سرچینې وګورئ.</div>';
    }catch(e){box.innerHTML='<div class="panel empty">د خبرونو د راوړلو پر مهال ستونزه رامنځته شوه.</div>';console.error(e);}
  };
  const oldShowPage=window.showPage;
  window.showPage=function(id){if(typeof oldShowPage==='function')oldShowPage(id);if(id==='externalnews')renderExternalNews();};

  // Real OOXML files. The existing editor remains the same; the server produces .xlsx/.docx.
  function downloadBlob(blob,name){const objectUrl=URL.createObjectURL(blob);const a=document.createElement('a');a.href=objectUrl;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(objectUrl),2500);}
  window.xSave=async function(){
    try{
      const cells={};for(const key of Object.keys(XS.v||{})){const [r,c]=key.split(',').map(Number);const st=XS.st[key]||{};cells[`${r},${c}`]={v:XS.v[key],st};}
      const name=(document.getElementById('xfile').value||'sheet').replace(/\.(xlsx|xls)$/i,'');
      const data={filename:name,rtl:false,sheets:[{name:'Sheet1',cells}]};
      const blob=await api(API_URL.xlsx,{method:'POST',body:JSON.stringify(data)});downloadBlob(blob,name+'.xlsx');
    }catch(e){reportError(e);}
  };
  window.wSave=async function(){
    try{const name=(document.getElementById('wfile').value||'document').replace(/\.(docx|doc)$/i,'');const blob=await api(API_URL.docx,{method:'POST',body:JSON.stringify({filename:name,html:document.getElementById('wdoc').innerHTML,rtl:document.getElementById('wdoc').dir==='rtl'})});downloadBlob(blob,name+'.docx');}
    catch(e){reportError(e);}
  };
  function officeOpenControls(){
    const xrow=document.querySelector('#offX .row:last-child');
    if(xrow&&!document.getElementById('xopen')){const b=document.createElement('button');b.className='btn light';b.textContent='پرانیستل .xlsx';b.onclick=()=>document.getElementById('xopen').click();xrow.appendChild(b);const i=document.createElement('input');i.type='file';i.accept='.xlsx';i.hidden=true;i.id='xopen';i.onchange=()=>officeImport(i.files[0]);xrow.appendChild(i);}
    const wrow=document.querySelector('#offW .row:last-child');
    if(wrow&&!document.getElementById('wopen')){const b=document.createElement('button');b.className='btn light';b.textContent='پرانیستل .docx';b.onclick=()=>document.getElementById('wopen').click();wrow.appendChild(b);const i=document.createElement('input');i.type='file';i.accept='.docx';i.hidden=true;i.id='wopen';i.onchange=()=>officeImport(i.files[0]);wrow.appendChild(i);}
  }
  async function officeImport(file){
    if(!file)return;const f=new FormData();f.append('file',file,file.name);
    try{const data=await api(API_URL.officeImport,{method:'POST',body:f});
      if(data.kind==='docx'){offTab('w');document.getElementById('wdoc').innerHTML=data.html||'';}
      else if(data.kind==='xlsx'){offTab('x');const sh=data.data?.sheets?.[0];if(sh){XS.rows=Math.max(30,sh.rows||30);XS.cols=Math.max(26,sh.cols||26);XS.v={};XS.st={};for(const [k,v] of Object.entries(sh.cells||{})){if(v.v!==undefined)XS.v[k]=String(v.v);if(v.st)XS.st[k]=v.st;}xBuild();} }
      note('فایل پرانیستل شو.');
    }catch(e){reportError(e);}
  }
  const oldOffInit=window.offInit;
  window.offInit=function(){if(typeof oldOffInit==='function')oldOffInit();officeOpenControls();};

  // Keep the visible editor's «Other reports» category, and include it in filtering.
  const oldRenderDept=window.renderDepartmentDocs;
  window.renderDepartmentDocs=function(){
    let list=vdocs().filter(d=>d.dept===currentDept).sort((a,b)=>b.ts-a.ts);
    if(deptPeriod!=='ټول')list=list.filter(d=>d.period===deptPeriod);
    document.getElementById('departmentDocs').innerHTML=tableHTML(docRows(list),t('empty_nodoc'));
  };

  // Server-side state refresh and notification polling.
  async function pollState(){if(document.visibilityState==='visible' && !document.getElementById('gate')?.style.display?.includes('grid')) await loadServerState();}
  async function setupPush(vapid){
    try{
      const reg=await navigator.serviceWorker.register('/sw.js');
      let sub=await reg.pushManager.getSubscription();
      if(!sub){const encoded=vapid.replace(/-/g,'+').replace(/_/g,'/');const key=Uint8Array.from(atob(encoded+'='.repeat((4-encoded.length%4)%4)),c=>c.charCodeAt(0));sub=await reg.pushManager.subscribe({userVisibleOnly:true,applicationServerKey:key});}
      const json=sub.toJSON();await api('/api/push/subscribe/',{method:'POST',body:JSON.stringify({endpoint:json.endpoint,keys:json.keys})});
    }catch(e){console.warn('Push permission/subscription not enabled',e);}
  }
  async function boot(){
    ensureExternalNewsUI();
    // Remove any saved demo-session identity and AI API secret from the browser.
    try{localStorage.removeItem('agency_session');localStorage.removeItem('agency_ai_key');if(typeof STATE_KEY!=='undefined')localStorage.removeItem(STATE_KEY);localStorage.removeItem('agency_demo_docs');localStorage.removeItem('agency_demo_news');}catch(_){}
    await loadServerState();
    if(!serverMe){const gate=document.getElementById('gate');if(gate)gate.style.display='grid';if(typeof gateMode==='function')gateMode(true);}
    // Retry unread/new state and news without a foreground page refresh.
    setInterval(()=>{if(document.visibilityState==='visible')loadServerState();},45000);
    setInterval(()=>{if(document.visibilityState==='visible'&&document.getElementById('externalnews')?.classList.contains('active'))renderExternalNews();},120000);
    // Registration verification resend helper.
    const sw=document.getElementById('gSw'); if(sw&&!document.getElementById('gVerifyAgain')){const b=document.createElement('button');b.id='gVerifyAgain';b.type='button';b.className='btn light';b.textContent='د تایید ایمیل لینک بیا ولېږه';b.style.display='none';b.onclick=()=>resendVerification();sw.after(b);}
    const pageTitle=document.getElementById('pageTitle');if(pageTitle&&serverMe)pageTitle.title='د Django سرور سره نښلول شوی';
    if(document.getElementById('aiKey'))document.getElementById('aiKey').remove();
    officeOpenControls();
    const nhead=document.querySelector('#notifications .section-head');
    if(nhead && !document.getElementById('enablePushBtn')){
      const b=document.createElement('button');b.id='enablePushBtn';b.className='btn light';b.textContent='په موبایل کې خبرتیاوې فعالول';
      b.onclick=async()=>{try{if(!('Notification' in window)){note('دا براوزر Push خبرتیا نه ملاتړ کوي.');return;}const permission=await Notification.requestPermission();if(permission!=='granted'){note('د خبرتیا اجازه ورنه کړل شوه.');return;}if(!publicVapidKey){note('د سرور VAPID کلیدونه نه دي تنظیم شوي.');return;}await setupPush(publicVapidKey);note('د موبایل خبرتیاوې فعالې شوې.');}catch(e){reportError(e);}};
      nhead.appendChild(b);
    }
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
