(() => {
  const el = id => document.getElementById(id);
  let selected = [], running = false, available = false, activeKey = null, outcome = false;
  function show() {
    el('dashboard').hidden = el('editor').hidden = true;
    el('word-editor').hidden = false;
    ['nav-home','nav-watermark'].forEach(id=>el(id).classList.remove('active'));
    el('nav-word').classList.add('active');el('breadcrumb').textContent='Word sang PDF';
    if(location.hash!=='#word')location.hash='word';
    window.scrollTo(0,0);
  }
  el('open-word').onclick=el('nav-word').onclick=show;
  el('word-back').onclick=()=>el('nav-home').click();
  window.addEventListener('hashchange',()=>{if(location.hash==='#word')show();});
  if(location.hash==='#word')show();
  function size(bytes) {return bytes<1024*1024 ? Math.max(1,Math.ceil(bytes/1024))+' KB' : (bytes/1024/1024).toFixed(1)+' MB';}
  function inputError(text) {el('word-input-error').textContent=text;el('word-input-error').hidden=!text;}
  function resetOutcome() {
    if(!outcome)return;
    outcome=false;el('word-run').hidden=true;el('word-result-panel').hidden=true;el('word-downloads').replaceChildren();
  }
  function render() {
    const locked=running||!!activeKey;
    el('word-list').replaceChildren();
    selected.forEach((file,index)=>{
      const row=document.createElement('div');row.className='file-row';
      const icon=document.createElement('span');icon.className='word-file-icon';icon.textContent=file.name.toLowerCase().endsWith('.docx')?'DOCX':'DOC';icon.setAttribute('aria-hidden','true');
      const name=document.createElement('span');name.className='name';name.textContent=file.name;name.title=file.name;
      const amount=document.createElement('small');amount.textContent=size(file.size);
      const remove=document.createElement('button');remove.type='button';remove.textContent='×';remove.disabled=locked;remove.setAttribute('aria-label','Bỏ '+file.name);
      remove.onclick=()=>{selected.splice(index,1);resetOutcome();inputError('');render();};row.append(icon,name,amount,remove);el('word-list').append(row);
    });
    el('word-selection').hidden=!selected.length;el('word-count').textContent=selected.length+' tài liệu';
    el('word-size').textContent=size(selected.reduce((n,f)=>n+f.size,0))+' / 195 MB';
    el('word-clear').hidden=!selected.length;el('word-clear').disabled=el('word-files').disabled=locked;
    el('word-drop').classList.toggle('word-drop-disabled',locked);
    el('word-start').disabled=locked||!available||!selected.length;
    el('word-start').hidden=outcome&&el('word-downloads').querySelector('.primary')!==null;
    el('word-start').textContent=running?'Đang chuyển đổi…':activeKey?'Đang chờ kết nối lại':outcome?'Chuyển lại tài liệu':'Chuyển '+(selected.length?selected.length+' file ':'')+'sang PDF';
    el('word-hint').textContent=activeKey&&!running?'Lượt chuyển vẫn có thể đang chạy. Kết nối lại để xem kết quả.':running?'Bạn có thể chuyển sang công cụ khác trong lúc chờ.':outcome?'Thêm hoặc bỏ file để bắt đầu lượt mới.':!available?'Bộ chuyển đổi chưa sẵn sàng.':selected.length?'Sẵn sàng chuyển đổi. Kết quả tải về dạng ZIP.':'Chọn tài liệu để bắt đầu.';
  }
  function add(incoming) {
    if(running||activeKey)return;
    const additions=[...incoming];if(!additions.length)return;
    if(additions.some(f=>! /\.(doc|docx)$/i.test(f.name)))return inputError('Chỉ hỗ trợ DOC và DOCX. Hãy chọn lại tài liệu Word.');
    const next=[...selected];let duplicates=0;
    for(const file of additions){if(next.some(f=>f.name===file.name&&f.size===file.size&&f.lastModified===file.lastModified))duplicates++;else next.push(file);}
    if(next.length>100||next.reduce((n,f)=>n+f.size,0)>195*1024*1024)return inputError('Mỗi lượt tối đa 100 file, tổng dung lượng 195 MB. Hãy chia thành nhiều lượt.');
    selected=next;resetOutcome();inputError(duplicates?'Đã bỏ qua '+duplicates+' file được chọn trùng.':'');render();
  }
  el('word-files').onchange=e=>{add(e.target.files);e.target.value='';};
  el('word-clear').onclick=()=>{selected=[];resetOutcome();inputError('');render();};
  ['dragenter','dragover'].forEach(type=>el('word-drop').addEventListener(type,e=>{e.preventDefault();if(!running&&!activeKey)el('word-drop').classList.add('drag');}));
  ['dragleave','drop'].forEach(type=>el('word-drop').addEventListener(type,e=>{e.preventDefault();el('word-drop').classList.remove('drag');}));
  el('word-drop').addEventListener('drop',e=>add(e.dataTransfer.files));
  async function body(response){const data=await response.json();if(!response.ok){const error=new Error(data.error||'Không xử lý được yêu cầu.');error.status=response.status;throw error;}return data;}
  function link(key,kind,label){const a=document.createElement('a');a.href=`/api/jobs/${key}/${kind}`;a.textContent=label;a.className=kind==='result'?'primary':'word-log';a.download='';el('word-downloads').append(a);}
  function remember(key){activeKey=key;if(key)localStorage.setItem('paperdesk-word-job',key);else localStorage.removeItem('paperdesk-word-job');}
  function reports(job){
    el('word-result-panel').hidden=!job.reports.length;el('word-summary').textContent=job.success+' thành công · '+job.failed+' lỗi';
    el('word-results').replaceChildren();
    job.reports.forEach(report=>{
      const row=document.createElement('div');const ok=report.status==='ok';row.className='word-result'+(ok?'':' failed');
      const content=document.createElement('div');const name=document.createElement('strong');name.textContent=report.file;
      const detail=document.createElement('small');detail.textContent=ok?report.output+' · '+report.pages+' trang':report.error;
      content.append(name,detail);const state=document.createElement('span');state.className='word-result-state';state.textContent=ok?'✓ Đã chuyển':'Chưa chuyển';row.append(content,state);el('word-results').append(row);
    });
  }
  async function follow(key) {
    running=true;remember(key);render();el('word-run').hidden=false;el('word-run').className='';el('word-progress').hidden=false;el('word-retry').hidden=true;el('word-downloads').replaceChildren();link(key,'log','Tải nhật ký xử lý');
    try {
      while(true){
        const job=await body(await fetch('/api/jobs/'+key));
        el('word-progress').max=job.total;el('word-progress').value=job.completed;
        el('word-status').textContent=job.state==='queued'?'Đang chờ xử lý…':`Đang chuyển ${job.completed}/${job.total} file`;
        el('word-current').textContent=job.current||'Lượt chuyển sẽ bắt đầu khi công cụ sẵn sàng.';reports(job);
        if(job.state==='completed'){
          outcome=true;el('word-run').className=job.success?'completed':'failed';
          el('word-status').textContent=job.success?`Đã chuyển ${job.success}/${job.total} file`:'Chưa có file nào chuyển thành công';
          el('word-current').textContent=job.failed?`${job.failed} file lỗi. Xem chi tiết bên dưới.`:'PDF đã sẵn sàng tải xuống.';
          el('word-downloads').replaceChildren();if(job.success)link(key,'result','↓ Tải '+job.success+' PDF (.zip)');link(key,'log','Tải nhật ký xử lý');
          remember(null);break;
        }
        if(job.state==='error'){remember(null);outcome=true;throw new Error(job.error);}
        await new Promise(resolve=>setTimeout(resolve,700));
      }
    }catch(error){
      if(error.status===404){remember(null);outcome=true;el('word-downloads').replaceChildren();}
      el('word-run').className='failed';el('word-status').textContent=activeKey?'Mất kết nối tiến trình': 'Không thể hoàn tất lượt chuyển';
      el('word-current').textContent=error.message;el('word-retry').hidden=!activeKey;el('word-progress').hidden=true;
    }finally{running=false;render();}
  }
  el('word-retry').onclick=()=>{if(activeKey&&!running)follow(activeKey);};
  el('word-start').onclick=async()=>{
    if(running||activeKey||!available||!selected.length)return;
    resetOutcome();inputError('');running=true;render();el('word-run').hidden=false;el('word-run').className='';el('word-progress').hidden=false;el('word-progress').removeAttribute('value');el('word-status').textContent='Đang gửi tài liệu…';el('word-current').textContent='Giữ trang mở đến khi tải tài liệu hoàn tất.';
    try{const data=new FormData();selected.forEach(f=>data.append('documents',f));const job=await body(await fetch('/api/word/jobs',{method:'POST',body:data}));await follow(job.id);}
    catch(error){el('word-run').className='failed';el('word-status').textContent='Chưa gửi được tài liệu';el('word-current').textContent=error.message;el('word-progress').hidden=true;}
    finally{running=false;render();}
  };
  fetch('/api/word/status').then(body).then(data=>{available=data.available;el('word-engine').textContent=available?'● Sẵn sàng':'Cần cài LibreOffice';el('word-engine').className='word-badge '+(available?'ready':'error');if(!available)inputError('Cài LibreOffice rồi khởi động lại ứng dụng. Nếu đã cài ở vị trí khác, đặt LIBREOFFICE_PATH trỏ tới bộ chuyển đổi.');render();}).catch(()=>{el('word-engine').textContent='Không kết nối được';el('word-engine').className='word-badge error';inputError('Không kết nối được ứng dụng. Hãy tải lại trang.');});
  const saved=localStorage.getItem('paperdesk-word-job');if(saved&&/^[a-f0-9]{32}$/.test(saved)){show();follow(saved);}
})();
