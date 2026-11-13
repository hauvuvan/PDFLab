const $ = s => document.querySelector(s);
let files = [], logoURL, previewURL, downloadURL, busy = false, revision = 0, savedLogo = null, presets = [];
const form = $('#watermark-form');
function navigate(editor) {
  $('#word-editor').hidden = true; $('#nav-word').classList.remove('active');
  $('#dashboard').hidden = editor; $('#editor').hidden = !editor;
  $('#nav-home').classList.toggle('active', !editor); $('#nav-watermark').classList.toggle('active', editor);
  $('#breadcrumb').textContent = editor ? 'Watermark PDF' : 'Tổng quan';
  location.hash = editor ? 'watermark' : ''; window.scrollTo(0,0);
}
$('#nav-home').onclick = $('#back').onclick = () => navigate(false);
$('#nav-watermark').onclick = $('#open-watermark').onclick = () => navigate(true);
window.addEventListener('hashchange', () => navigate(location.hash === '#watermark'));
if(location.hash === '#watermark') navigate(true);
function message(text, error=false) { $('#status').hidden=false; $('#status').textContent=text; $('#status').classList.toggle('error',error); }
function stale() {revision++; if(!$('#preview-image').hidden) $('#preview-note').textContent='Cấu hình đã thay đổi. Bấm “Xem” để cập nhật bản xem trước.';}
function renderFiles(){
  $('#file-list').replaceChildren(); $('#preview-file').replaceChildren();
  files.forEach((file,i)=>{
    const row=document.createElement('div');row.className='file-row';
    const name=document.createElement('span');name.className='name';name.textContent=file.name;name.title=file.name;
    const size=document.createElement('small');size.textContent=(file.size/1024/1024).toFixed(1)+' MB';
    const remove=document.createElement('button');remove.type='button';remove.textContent='×';remove.setAttribute('aria-label','Bỏ '+file.name);remove.onclick=()=>{files.splice(i,1);renderFiles();stale();};
    row.append(name,size,remove);$('#file-list').append(row);
    const option=document.createElement('option');option.value=i;option.textContent=file.name;$('#preview-file').append(option);
  });
  if(!files.length){const option=document.createElement('option');option.textContent='Chưa chọn PDF';option.value='';$('#preview-file').append(option);}
  $('#file-count').textContent=files.length ? files.length+' file đã chọn' : 'Chưa có file';
}
function addFiles(incoming){
  const all=[...files,...incoming];
  if(all.some(f=>!f.name.toLowerCase().endsWith('.pdf'))) return message('Chỉ chọn file PDF.',true);
  if(all.length>100) return message('Mỗi lượt tối đa 100 file PDF.',true);
  if(all.reduce((n,f)=>n+f.size,0)>195*1024*1024) return message('PDF vượt 195 MB. Hãy chia nhỏ để dành dung lượng cho ảnh watermark.',true);
  files=all;renderFiles();stale();
}
$('#pdfs').onchange=e=>{addFiles(e.target.files);e.target.value='';};
const drop=$('#dropzone');
['dragenter','dragover'].forEach(event=>drop.addEventListener(event,e=>{e.preventDefault();drop.classList.add('drag');}));
['dragleave','drop'].forEach(event=>drop.addEventListener(event,e=>{e.preventDefault();drop.classList.remove('drag');}));
drop.addEventListener('drop',e=>addFiles(e.dataTransfer.files));
$('#watermark').onchange=e=>{
  const file=e.target.files[0];savedLogo=null;stale();
  if(!file)return;
  if(file.size>15*1024*1024){e.target.value='';return message('Ảnh watermark tối đa 15 MB.',true);}
  if(logoURL)URL.revokeObjectURL(logoURL);logoURL=URL.createObjectURL(file);
  $('#logo-thumb').src=logoURL;$('#logo-thumb').hidden=false;$('#logo-placeholder').hidden=true;$('#logo-name').textContent=file.name;
};
const defaults={kind:'image',position:'bottom',margin:20,width:50,height:10,opacity:100,angle:0,offset_x:0,offset_y:0,spacing_x:20,spacing_y:15,layout:'single',layer:'above',font:'sans',bold:'false',color:'#808080',tint:'false',text:'tailieuchuan.vn',pages:'all',page_range:'',prefix:'[tailieuonthi.org]',link:'https://tailieuonthi.org/'};
function updateRanges(){
  for(const name of ['width','height'])$('#'+name+'-value').textContent=form.elements[name].value+'%';
  $('#angle-value').textContent=form.elements.angle.value+'°';
  $('#transparency-value').textContent=(100-Number(form.elements.opacity.value))+'%';
}
function syncUI(){
  const text=form.elements.kind.value==='text';
  $('#text-settings').hidden=!text;$('#image-settings').hidden=text;
  form.elements.text.required=text;
  $('#tile-settings').hidden=form.elements.layout.value!=='tile';
  $('#tile-settings').querySelectorAll('input').forEach(field=>field.disabled=$('#tile-settings').hidden);
  $('#page-range-label').hidden=form.elements.pages.value!=='custom';
  form.elements.page_range.required=form.elements.pages.value==='custom';
  form.elements.page_range.disabled=form.elements.pages.value!=='custom';
  document.querySelectorAll('[data-position]').forEach(button=>{button.setAttribute('aria-pressed',String(button.dataset.position===form.elements.position.value));button.disabled=form.elements.layout.value==='tile';});
  $('#transparency').value=100-Number(form.elements.opacity.value);
  $('#color-hint').textContent=text ? 'Màu của chữ watermark.' : $('#tint-toggle').checked ? 'Đổi tất cả điểm ảnh có màu thành màu này, giữ alpha.' : 'Ảnh đang giữ màu gốc. Bật “Đổi ảnh thành một màu” để áp dụng.';
  updateRanges();
}
function setOptions(values){for(const [name,value] of Object.entries(values)){const field=form.elements[name];if(field)field.value=String(value);}$('#tint-toggle').checked=values.tint==='true';syncUI();stale();}
form.addEventListener('input',e=>{if(e.target.id==='transparency')form.elements.opacity.value=100-Number(e.target.value);syncUI();stale();});
form.addEventListener('change',syncUI);
$('#preview-file').onchange=stale;$('#page-number').oninput=stale;
document.querySelectorAll('[data-position]').forEach(button=>button.onclick=()=>{form.elements.position.value=button.dataset.position;syncUI();stale();});
$('#reset').onclick=()=>setOptions(defaults);
$('#recipe-diagonal').onclick=()=>setOptions({...defaults,kind:'text',layout:'tile',bold:'true',position:'center',angle:30,opacity:35,width:38,height:35,spacing_x:18,spacing_y:12,link:'',prefix:'[watermark]'});
$('#recipe-footer').onclick=()=>setOptions(defaults);
function currentLogo(){return $('#watermark').files[0]||savedLogo;}
function currentOptions(){const data=new FormData(form);const values={};for(const key of Object.keys(defaults))values[key]=data.get(key)??defaults[key];values.tint=String($('#tint-toggle').checked);return values;}
syncUI();
function payload(preview){
  if(!form.reportValidity())return null;
  if(!files.length){message('Vui lòng thêm ít nhất một PDF.',true);return null;}
  const logo=currentLogo();if(form.elements.kind.value==='image'&&!logo){message('Vui lòng chọn ảnh watermark.',true);return null;}
  const data=new FormData(form);data.set('tint',String($('#tint-toggle').checked));if(logo)data.append('watermark',logo,'watermark.png');
  if(preview){data.append('pdf',files[Number($('#preview-file').value)||0]);data.append('page',$('#page-number').value);}else files.forEach(file=>data.append('pdfs',file));
  return data;
}
function setBusy(value){busy=value;$('#process-button').disabled=value;$('#preview-button').disabled=value;document.querySelectorAll('.preset-actions button,#preset-apply,#preset-import').forEach(el=>el.disabled=value);}
async function errorBody(response){try{return await response.json();}catch{return {error:'Không đọc được phản hồi. Hãy thử chia nhỏ số file hoặc khởi động lại công cụ.'};}}
$('#preview-button').onclick=async()=>{
  if(busy)return;const data=payload(true);if(!data)return;setBusy(true);const current=revision;message('Đang tạo bản xem trước…');
  try{const response=await fetch('/api/preview',{method:'POST',body:data});if(!response.ok)throw new Error((await errorBody(response)).error);
    const blob=await response.blob();if(previewURL)URL.revokeObjectURL(previewURL);previewURL=URL.createObjectURL(blob);$('#preview-image').src=previewURL;$('#preview-image').hidden=false;$('#preview-empty').hidden=true;
    $('#preview-note').textContent=current===revision ? `Trang ${data.get('page')} / ${response.headers.get('X-Page-Count')} · Đúng cấu hình xuất file` : 'Cấu hình đã thay đổi. Bấm “Xem” để cập nhật.';message('Đã tạo bản xem trước. Kiểm tra vị trí trước khi xử lý hàng loạt.');
  }catch(error){message(error.message,true);}finally{setBusy(false);}
};
function reports(items){const box=$('#results');box.hidden=false;for(const item of items){const p=document.createElement('p');p.textContent=item.status==='ok' ? `✓ ${item.file} → ${item.output} · ${item.pages} trang` : `⚠ ${item.file}: ${item.error}`;box.append(p);}}
function jobLink(key, kind, label) {
  const link=document.createElement('a');link.href=`/api/jobs/${key}/${kind}`;link.className='download';link.textContent=label;$('#results').append(link);$('#results').hidden=false;return link;
}
const pause = ms => new Promise(resolve=>setTimeout(resolve,ms));
async function followJob(key){
  let shown=0, retries=0;
  jobLink(key,'log','↓ Tải log tiến trình và lỗi');
  while(true){
    let job;
    try {
      const response=await fetch(`/api/jobs/${key}`);
      if(!response.ok)throw new Error((await errorBody(response)).error);
      job=await response.json();retries=0;
    } catch(error) {
      if(++retries>=5)throw new Error('Không đọc được tiến trình. Tải log bên dưới để kiểm tra; tải lại trang để thử kết nối lại.');
      message('Kết nối gián đoạn, đang thử đọc lại tiến trình…',true);await pause(1500);continue;
    }
    if(job.reports.length>shown){reports(job.reports.slice(shown));shown=job.reports.length;}
    $('#job-progress').value=job.completed;
    $('#job-progress').max=job.total;
    message(`${job.state==='queued'?'Đang chờ':'Đang xử lý'} · ${job.completed}/${job.total} file hoàn tất · ${job.success} thành công, ${job.failed} lỗi`+
      (job.current ? ` · ${job.current} · trang ${job.page}/${job.pages||'…'}` : ''));
    if(job.state==='completed'){
      if(job.success)jobLink(key,'result','↓ Tải ZIP kết quả và log').click();
      message(`Hoàn tất ${job.completed}/${job.total} file: ${job.success} thành công, ${job.failed} lỗi. Log lưu tiến trình và chi tiết lỗi.`,job.failed>0);
      localStorage.removeItem('paperdesk-job');return;
    }
    if(job.state==='error'){localStorage.removeItem('paperdesk-job');throw new Error(job.error);}
    await pause(600);
  }
}
async function trackJob(key){
  setBusy(true);$('#results').replaceChildren();$('#results').hidden=true;$('#job-progress').hidden=false;
  try{await followJob(key);}catch(error){message(error.message||'Kết nối bị gián đoạn.',true);}finally{setBusy(false);}
}
form.onsubmit=async e=>{
  e.preventDefault();if(busy)return;const data=payload(false);if(!data)return;setBusy(true);message('Đang tải tài liệu lên máy xử lý…');
  try{
    const response=await fetch('/api/jobs',{method:'POST',body:data});
    if(!response.ok)throw new Error((await errorBody(response)).error);
    const job=await response.json();localStorage.setItem('paperdesk-job',job.id);await trackJob(job.id);
  }catch(error){message(error.message||'Kết nối bị gián đoạn. Hãy thử lại.',true);}finally{setBusy(false);}
};
const savedJob=localStorage.getItem('paperdesk-job');
if(savedJob && /^[a-f0-9]{32}$/.test(savedJob)){navigate(true);trackJob(savedJob);}

// Presets live in the local application folder and include only settings + logo.
async function refreshPresets(selected=''){
  const response=await fetch('/api/presets');const body=await response.json();if(!response.ok)throw new Error(body.error);
  presets=body.presets;const select=$('#preset-select');select.replaceChildren(new Option('Chọn mẫu đã lưu…',''));
  presets.forEach(p=>select.append(new Option(p.name,p.id)));select.value=selected;
}
function selectedPreset(){return presets.find(p=>p.id===$('#preset-select').value);}
function fileBase64(file){return new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result.split(',')[1]);reader.onerror=()=>reject(new Error('Không đọc được logo.'));reader.readAsDataURL(file);});}
async function recipeData(update=false){
  const name=$('#preset-name').value.trim();if(!name)throw new Error('Nhập tên mẫu trước khi lưu.');
  const opts=currentOptions();let image='';
  if(opts.kind==='image'){const logo=currentLogo();if(!logo)throw new Error('Chọn ảnh để lưu cùng mẫu.');image=await fileBase64(logo);}
  const data={name,options:opts,image};if(update){const item=selectedPreset();if(!item)throw new Error('Chọn mẫu cần cập nhật.');data.id=item.id;}return data;
}
async function persistRecipe(data){const response=await fetch('/api/presets',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const body=await response.json();if(!response.ok)throw new Error(body.error);await refreshPresets(body.preset.id);$('#preset-name').value=body.preset.name;return body.preset;}
for(const [id,update] of [['preset-save',false],['preset-update',true]])$('#'+id).onclick=async()=>{
  if(busy)return;try{const data=await recipeData(update);setBusy(true);await persistRecipe(data);message(update?'Đã cập nhật mẫu trên máy.':'Đã lưu mẫu mới trên máy, gồm cấu hình và logo nếu có.');}catch(error){message(error.message,true);}finally{setBusy(false);}
};
$('#preset-select').onchange=()=>{const item=selectedPreset();$('#preset-name').value=item?item.name:'';};
function applyRecipe(item){
  setOptions(item.options);$('#watermark').value='';savedLogo=null;
  if(logoURL)URL.revokeObjectURL(logoURL);
  if(item.options.kind==='image'){
    const bytes=Uint8Array.from(atob(item.image),c=>c.charCodeAt(0));savedLogo=new Blob([bytes],{type:'image/png'});logoURL=URL.createObjectURL(savedLogo);$('#logo-thumb').src=logoURL;$('#logo-thumb').hidden=false;$('#logo-placeholder').hidden=true;$('#logo-name').textContent='Logo từ mẫu: '+item.name;
  }else{$('#logo-thumb').hidden=true;$('#logo-placeholder').hidden=false;$('#logo-name').textContent='Chọn logo hoặc hình ảnh';}
  $('#preset-name').value=item.name;message('Đã áp dụng mẫu “'+item.name+'”. Bấm Xem để kiểm tra trên PDF.');
}
$('#preset-apply').onclick=()=>{const item=selectedPreset();if(!item)return message('Chọn mẫu trước khi áp dụng.',true);applyRecipe(item);};
$('#preset-delete').onclick=async()=>{
  const item=selectedPreset();if(!item)return message('Chọn mẫu cần xóa.',true);
  if(!confirm('Xóa mẫu “'+item.name+'” khỏi máy? Bạn có thể xuất JSON để sao lưu trước.'))return;
  setBusy(true);try{const response=await fetch('/api/presets/'+encodeURIComponent(item.id),{method:'DELETE'});const body=await response.json();if(!response.ok)throw new Error(body.error);await refreshPresets();$('#preset-name').value='';message('Đã xóa mẫu.');}catch(error){message(error.message,true);}finally{setBusy(false);}
};
$('#preset-export').onclick=()=>{
  const item=selectedPreset();if(!item)return message('Chọn mẫu đã lưu để xuất JSON.',true);
  const data={format:'paperdesk-watermark',version:1,name:item.name,options:item.options,image:item.image};
  const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const link=document.createElement('a');link.href=url;link.download='paperdesk-watermark.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),60000);message('Đã xuất bản sao mẫu JSON. File này có chứa logo và nội dung chữ.');
};
$('#preset-import').onchange=async e=>{
  const file=e.target.files[0];if(!file)return;setBusy(true);
  try{if(file.size>22*1024*1024)throw new Error('File mẫu tối đa 22 MB.');const data=JSON.parse(await file.text());if(data.format!=='paperdesk-watermark'||data.version!==1)throw new Error('Định dạng mẫu Paperdesk không hợp lệ.');delete data.id;const item=await persistRecipe(data);applyRecipe(item);message('Đã nhập và lưu mẫu “'+item.name+'” trên máy.');}catch(error){message(error.message,true);}finally{e.target.value='';setBusy(false);}
};
refreshPresets().catch(error=>message(error.message,true));
