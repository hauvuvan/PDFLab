(() => {
  const el = id => document.getElementById(id);
  let selected = [], running = false, available = false;
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
  function status(text) {el('word-status').textContent=text;}
  function render() {
    el('word-list').replaceChildren();
    selected.forEach((file,index)=>{
      const row=document.createElement('div');row.className='file-row';
      const name=document.createElement('span');name.className='name';name.textContent=file.name;
      const size=document.createElement('small');size.textContent=(file.size/1024/1024).toFixed(1)+' MB';
      const remove=document.createElement('button');remove.type='button';remove.textContent='×';remove.disabled=running;remove.setAttribute('aria-label','Bỏ '+file.name);
      remove.onclick=()=>{selected.splice(index,1);render();};row.append(name,size,remove);el('word-list').append(row);
    });
    el('word-count').textContent=selected.length+' file đã chọn';
    el('word-start').disabled=running||!available||!selected.length;
    el('word-clear').disabled=el('word-files').disabled=running;
  }
  function add(incoming) {
    if(running)return;
    const next=[...selected,...incoming];
    if(next.some(f=>! /\.(doc|docx)$/i.test(f.name)))return status('Chỉ chọn file .doc hoặc .docx.');
    if(next.length>100||next.reduce((n,f)=>n+f.size,0)>195*1024*1024)return status('Mỗi lượt tối đa 100 file và 195 MB.');
    selected=next;render();status('');
  }
  el('word-files').onchange=e=>{add(e.target.files);e.target.value='';};
  el('word-clear').onclick=()=>{selected=[];render();};
  ['dragover','drop'].forEach(type=>el('word-drop').addEventListener(type,e=>e.preventDefault()));
  el('word-drop').addEventListener('drop',e=>add(e.dataTransfer.files));
  async function body(response){const data=await response.json();if(!response.ok)throw new Error(data.error||'Không xử lý được yêu cầu.');return data;}
  function link(key,kind,label){const a=document.createElement('a');a.href=`/api/jobs/${key}/${kind}`;a.textContent=label;a.className='secondary';a.download='';el('word-downloads').append(a);}
  async function follow(key) {
    running=true;render();el('word-progress').hidden=false;el('word-results').replaceChildren();el('word-downloads').replaceChildren();
    link(key,'log','Tải log');
    try {
      while(true){
        const job=await body(await fetch('/api/jobs/'+key));
        el('word-progress').max=job.total;el('word-progress').value=job.completed;
        status(`${job.state==='queued'?'Đang chờ': 'Đang chuyển'} · ${job.completed}/${job.total} file · ${job.success} thành công, ${job.failed} lỗi${job.current?' · '+job.current:''}`);
        el('word-results').replaceChildren();
        job.reports.forEach(report=>{const row=document.createElement('p');row.textContent=report.file+' — '+(report.status==='ok'?report.pages+' trang → '+report.output:report.error);el('word-results').append(row);});
        if(job.state==='completed'){
          status(`Hoàn tất: ${job.success} thành công, ${job.failed} lỗi.`);
          if(job.success)link(key,'result','↓ Tải ZIP PDF và báo cáo');
          localStorage.removeItem('paperdesk-word-job');break;
        }
        if(job.state==='error'){localStorage.removeItem('paperdesk-word-job');throw new Error(job.error);}
        await new Promise(resolve=>setTimeout(resolve,700));
      }
    }catch(error){status(error.message+' Có thể tải lại trang để nối lại tiến trình.');}
    finally{running=false;render();}
  }
  el('word-start').onclick=async()=>{
    if(running||!selected.length)return;
    running=true;render();status('Đang tải tài liệu lên…');
    try{const data=new FormData();selected.forEach(f=>data.append('documents',f));const job=await body(await fetch('/api/word/jobs',{method:'POST',body:data}));localStorage.setItem('paperdesk-word-job',job.id);await follow(job.id);}
    catch(error){status(error.message);}finally{running=false;render();}
  };
  fetch('/api/word/status').then(body).then(data=>{available=data.available;el('word-engine').textContent=available?'Sẵn sàng · Xử lý cục bộ bằng LibreOffice':'Cần cài LibreOffice, hoặc cấu hình LIBREOFFICE_PATH và khởi động lại ứng dụng.';render();}).catch(()=>{el('word-engine').textContent='Không kết nối được bộ chuyển đổi. Hãy tải lại trang.';});
  const saved=localStorage.getItem('paperdesk-word-job');if(saved&&/^[a-f0-9]{32}$/.test(saved)){show();follow(saved);}
})();
