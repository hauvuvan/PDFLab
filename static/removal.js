const q=s=>document.querySelector(s);
let files=[], sampleIndex=0, candidates=[], images=new Set(), regions=[], after=false, busy=false, url=null, start=null, draft=null;

const getSource=()=>files[sampleIndex]||null;

function status(text){q('#status').textContent=text;}

function formatSize(b){
  if(b<1024)return b+' B';
  if(b<1024*1024)return (b/1024).toFixed(1)+' KB';
  return (b/1024/1024).toFixed(1)+' MB';
}

function controls(){
  const s=getSource();
  document.querySelectorAll('button,input,select').forEach(e=>e.disabled=busy);
  ['load','preview','export','original'].forEach(id=>{const el=q('#'+id);if(el)el.disabled=busy||!s;});
  const singleBtn=q('#export-single');
  if(singleBtn){singleBtn.disabled=busy||!s;singleBtn.hidden=files.length<=1;}
  const exportBtn=q('#export');
  if(exportBtn){
    exportBtn.textContent=files.length>1?`Xoá hàng loạt (${files.length} file)`:'Xoá & tải PDF';
  }
  q('#overlay').style.pointerEvents=busy||after?'none':'auto';
}

function place(el,r){
  Object.assign(el.style,{left:r[0]*100+'%',top:r[1]*100+'%',width:(r[2]-r[0])*100+'%',height:(r[3]-r[1])*100+'%'});
}

function draw(){
  q('#overlay').replaceChildren();
  q('#selection-list').replaceChildren();
  if(!after){
    if(q('#mode').value==='image')candidates.forEach((c,i)=>{
      const b=document.createElement('button');
      b.className=images.has(c.id)?'selected':'';
      b.title=`Ảnh ${i+1} · ${c.width}×${c.height}`;
      b.setAttribute('aria-label',b.title);
      b.setAttribute('aria-pressed',String(images.has(c.id)));
      place(b,c.rect);
      b.onclick=()=>{images.has(c.id)?images.delete(c.id):images.add(c.id);draw();};
      q('#overlay').append(b);
    });
    regions.forEach(r=>{
      const d=document.createElement('div');
      d.className='region';
      place(d,r);
      q('#overlay').append(d);
    });
  }
  const add=(text,fn)=>{
    const p=document.createElement('p');
    p.textContent=text;
    const b=document.createElement('button');
    b.type='button';
    b.textContent='Bỏ';
    b.onclick=fn;
    p.append(b);
    q('#selection-list').append(p);
  };
  [...images].forEach((id,i)=>add('Ảnh đã chọn '+(i+1),()=>{images.delete(id);draw();}));
  regions.forEach((r,i)=>add(`Vùng ${i+1} · ${(r[0]*100).toFixed(0)}%, ${(r[1]*100).toFixed(0)}% → ${(r[2]*100).toFixed(0)}%, ${(r[3]*100).toFixed(0)}%`,()=>{regions.splice(i,1);draw();}));
  controls();
}

function renderFiles(){
  const list=q('#file-list');
  list.replaceChildren();
  q('#file-count').textContent=files.length?`${files.length} file PDF`:'Chưa chọn file';
  files.forEach((file,i)=>{
    const row=document.createElement('div');
    row.className='file-row';
    if(i===sampleIndex){
      const badge=document.createElement('span');
      badge.className='badge-sample';
      badge.textContent='Mẫu';
      row.append(badge);
    }else{
      const btn=document.createElement('button');
      btn.type='button';
      btn.className='sample-btn';
      btn.textContent='Xem mẫu';
      btn.title='Chọn file này làm mẫu xem trước';
      btn.onclick=()=>{if(busy)return;sampleIndex=i;renderFiles();request('inspect');};
      row.append(btn);
    }
    const name=document.createElement('span');
    name.className='name';
    name.textContent=`${i+1}. ${file.name}`;
    name.title=file.name;
    row.append(name);
    const sz=document.createElement('small');
    sz.textContent=formatSize(file.size);
    row.append(sz);
    const del=document.createElement('button');
    del.type='button';
    del.textContent='×';
    del.title='Bỏ file';
    del.disabled=busy;
    del.onclick=()=>{
      if(busy)return;
      files.splice(i,1);
      if(sampleIndex>=files.length)sampleIndex=Math.max(0,files.length-1);
      renderFiles();
      if(files.length){
        request('inspect');
      }else{
        q('#document').hidden=true;
        q('#empty').hidden=false;
        after=false;
        candidates=[];
        draw();
        status('Mở PDF để bắt đầu.');
      }
    };
    row.append(del);
    list.append(row);
  });
  controls();
}

function addFiles(incoming){
  if(busy)return;
  const valid=[];
  for(const f of incoming){
    if(f.name.toLowerCase().endsWith('.pdf'))valid.push(f);
  }
  if(!valid.length){
    if(incoming.length)status('Chỉ hỗ trợ file định dạng PDF.');
    return;
  }
  const isFirst=files.length===0;
  for(const f of valid){
    if(!files.some(existing=>existing.name===f.name&&existing.size===f.size)){
      files.push(f);
    }
  }
  if(isFirst){
    sampleIndex=0;
    images.clear();
    regions=[];
    q('#page').value=1;
  }
  renderFiles();
  if(isFirst||!getSource()){
    request('inspect');
  }else{
    status(`Đã thêm file. Tổng cộng ${files.length} file PDF trong danh sách.`);
  }
}

function payload(isBatch=false){
  const f=new FormData();
  if(isBatch){
    files.forEach(file=>f.append('pdfs',file));
  }else{
    f.append('pdf',getSource());
  }
  f.set('page',q('#page').value);
  f.set('regions',JSON.stringify(regions));
  f.set('images',JSON.stringify([...images]));
  f.set('pages',q('#scope').value);
  f.set('page_range',q('#range').value);
  return f;
}

async function request(action){
  const s=getSource();
  if(busy||!s)return;
  const isBatch=action==='batch'||(action==='export'&&files.length>1);
  const actualAction=isBatch?'batch':(action==='single'?'export':action);
  busy=true;
  controls();
  status(isBatch?`Đang xử lý ${files.length} file PDF…`:'Đang xử lý…');
  try{
    const response=await fetch('/api/removal/'+actualAction,{method:'POST',body:payload(isBatch)});
    if(!response.ok){
      const body=await response.json();
      throw Error(body.error||'Lỗi khi xử lý.');
    }
    if(actualAction==='inspect'){
      const data=await response.json();
      candidates=data.candidates;
      q('#document').src='data:image/png;base64,'+data.image;
      q('#page-count').textContent=data.pages+' trang · '+candidates.length+' ảnh độc lập trên trang này';
      q('#page').max=data.pages;
      after=false;
      q('#document').hidden=false;
      q('#empty').hidden=true;
      q('#view-title').textContent='Bản gốc · chọn watermark';
      status('Đã mở trang. Chọn ảnh hoặc khoanh vùng.');
    }else if(actualAction==='preview'){
      const blob=await response.blob();
      if(url)URL.revokeObjectURL(url);
      url=URL.createObjectURL(blob);
      q('#document').src=url;
      after=true;
      q('#document').hidden=false;
      q('#empty').hidden=true;
      q('#view-title').textContent='Sau khi xoá · xem trước';
      status('Đã xem trước. Kiểm tra nội dung trước khi xuất.');
    }else{
      const blob=await response.blob();
      if(url)URL.revokeObjectURL(url);
      url=URL.createObjectURL(blob);
      const a=document.createElement('a');
      a.href=url;
      if(isBatch){
        a.download='da-xoa-watermark-hang-loat.zip';
        status(`Đã hoàn tất xoá watermark ${files.length} file (ZIP). File gốc được giữ nguyên.`);
      }else{
        const stem=(s?s.name:'tai-lieu').replace(/\.pdf$/i,'');
        a.download=`${stem}_da_xoa_watermark.pdf`;
        status('Đã tạo PDF. File gốc được giữ nguyên.');
      }
      a.click();
    }
    draw();
  }catch(e){
    status(e.message);
  }finally{
    busy=false;
    controls();
  }
}

q('#source').onchange=e=>{
  addFiles(e.target.files);
  e.target.value='';
};

const dropzone=q('#dropzone');
['dragenter','dragover'].forEach(name=>{
  dropzone.addEventListener(name,e=>{
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.add('drag');
  });
});
['dragleave','dragend'].forEach(name=>{
  dropzone.addEventListener(name,e=>{
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.remove('drag');
  });
});
dropzone.addEventListener('drop',e=>{
  e.preventDefault();
  e.stopPropagation();
  dropzone.classList.remove('drag');
  if(e.dataTransfer&&e.dataTransfer.files)addFiles(e.dataTransfer.files);
});

q('#load').onclick=q('#original').onclick=()=>request('inspect');
q('#preview').onclick=()=>request('preview');
q('#export').onclick=()=>request('export');
const singleBtn=q('#export-single');
if(singleBtn)singleBtn.onclick=()=>request('single');

q('#scope').onchange=()=>q('#range').hidden=q('#scope').value!=='custom';
q('#mode').onchange=()=>{
  q('#mode-help').textContent=q('#mode').value==='image'?'Bấm khung ảnh để chọn hoặc bỏ chọn. Ảnh trùng được áp dụng trên phạm vi trang đã chọn.':'Kéo để khoanh vùng. Vùng này sẽ xoá trắng tất cả nội dung bên trong.';
  draw();
};
q('#clear').onclick=()=>{
  images.clear();
  regions=[];
  draw();
  status('Đã bỏ lựa chọn. Mở lại bản gốc nếu đang xem kết quả.');
};

function point(e){
  const b=q('#overlay').getBoundingClientRect();
  return [Math.max(0,Math.min(1,(e.clientX-b.left)/b.width)),Math.max(0,Math.min(1,(e.clientY-b.top)/b.height))];
}

q('#overlay').onpointerdown=e=>{
  if(busy||after||q('#document').hidden||q('#mode').value!=='region')return;
  e.preventDefault();
  start=point(e);
  q('#overlay').setPointerCapture(e.pointerId);
  draft=document.createElement('div');
  draft.className='region';
  q('#overlay').append(draft);
};

q('#overlay').onpointermove=e=>{
  if(!start)return;
  const p=point(e);
  place(draft,[Math.min(start[0],p[0]),Math.min(start[1],p[1]),Math.max(start[0],p[0]),Math.max(start[1],p[1])]);
};

q('#overlay').onpointerup=e=>{
  if(!start)return;
  const p=point(e),r=[Math.min(start[0],p[0]),Math.min(start[1],p[1]),Math.max(start[0],p[0]),Math.max(start[1],p[1])];
  if(r[2]-r[0]>.003&&r[3]-r[1]>.003){
    if(regions.length<30)regions.push(r);else status('Tối đa 30 vùng.');
  }
  start=null;
  draw();
};

q('#overlay').onpointercancel=()=>{start=null;draw();};

renderFiles();
controls();
