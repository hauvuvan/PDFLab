const $ = s => document.querySelector(s);
let files = [], logoURL, previewURL, downloadURL, busy = false, revision = 0;
const form = $('#watermark-form');
function navigate(editor) {
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
  const file=e.target.files[0];stale();
  if(!file)return;
  if(file.size>15*1024*1024){e.target.value='';return message('Ảnh watermark tối đa 15 MB.',true);}
  if(logoURL)URL.revokeObjectURL(logoURL);logoURL=URL.createObjectURL(file);
  $('#logo-thumb').src=logoURL;$('#logo-thumb').hidden=false;$('#logo-placeholder').hidden=true;$('#logo-name').textContent=file.name;
};
function updateRanges(){for(const name of ['width','opacity'])$('#'+name+'-value').textContent=form.elements[name].value+'%';}
form.addEventListener('input',()=>{updateRanges();stale();});
$('#preview-file').onchange=stale;$('#page-number').oninput=stale;
$('#reset').onclick=()=>{for(const [name,value] of Object.entries({position:'bottom',margin:20,width:50,height:10,opacity:100,prefix:'[tailieuonthi.org]',link:'https://tailieuonthi.org/'}))form.elements[name].value=value;updateRanges();stale();};
function payload(preview){
  if(!form.reportValidity())return null;
  if(!files.length){message('Vui lòng thêm ít nhất một PDF.',true);return null;}
  const logo=$('#watermark').files[0];if(!logo){message('Vui lòng chọn ảnh watermark.',true);return null;}
  const data=new FormData(form);data.append('watermark',logo);
  if(preview){data.append('pdf',files[Number($('#preview-file').value)||0]);data.append('page',$('#page-number').value);}else files.forEach(file=>data.append('pdfs',file));
  return data;
}
function setBusy(value){busy=value;$('#process-button').disabled=value;$('#preview-button').disabled=value;}
async function errorBody(response){try{return await response.json();}catch{return {error:'Không đọc được phản hồi. Hãy thử chia nhỏ số file hoặc khởi động lại công cụ.'};}}
$('#preview-button').onclick=async()=>{
  if(busy)return;const data=payload(true);if(!data)return;setBusy(true);const current=revision;message('Đang tạo bản xem trước…');
  try{const response=await fetch('/api/preview',{method:'POST',body:data});if(!response.ok)throw new Error((await errorBody(response)).error);
    const blob=await response.blob();if(previewURL)URL.revokeObjectURL(previewURL);previewURL=URL.createObjectURL(blob);$('#preview-image').src=previewURL;$('#preview-image').hidden=false;$('#preview-empty').hidden=true;
    $('#preview-note').textContent=current===revision ? `Trang ${data.get('page')} / ${response.headers.get('X-Page-Count')} · Đúng cấu hình xuất file` : 'Cấu hình đã thay đổi. Bấm “Xem” để cập nhật.';message('Đã tạo bản xem trước. Kiểm tra vị trí trước khi xử lý hàng loạt.');
  }catch(error){message(error.message,true);}finally{setBusy(false);}
};
function reports(items){const box=$('#results');box.hidden=false;for(const item of items){const p=document.createElement('p');p.textContent=item.status==='ok' ? `✓ ${item.file} → ${item.output} · ${item.pages} trang` : `⚠ ${item.file}: ${item.error}`;box.append(p);}}
form.onsubmit=async e=>{
  e.preventDefault();if(busy)return;const data=payload(false);if(!data)return;setBusy(true);$('#results').replaceChildren();$('#results').hidden=true;message('Đang xử lý '+files.length+' file. Vui lòng giữ trang này mở…');
  try{const response=await fetch('/api/process',{method:'POST',body:data});if(!response.ok){const body=await errorBody(response);if(body.reports)reports(body.reports);throw new Error(body.error);}
    const blob=await response.blob();if(downloadURL)URL.revokeObjectURL(downloadURL);downloadURL=URL.createObjectURL(blob);
    const link=document.createElement('a');link.href=downloadURL;link.download='pdf-watermark.zip';link.className='download';link.textContent='↓ Tải lại file ZIP kết quả';$('#results').append(link);$('#results').hidden=false;link.click();
    const detail=JSON.parse(response.headers.get('X-Reports')||'[]');
    if(detail.length)reports(detail);else{const note=document.createElement('p');note.textContent='Danh sách kết quả đầy đủ nằm trong bao-cao.json bên trong ZIP.';$('#results').append(note);}
    const failed=Number(response.headers.get('X-Failure-Count'));message(`Hoàn tất ${response.headers.get('X-Success-Count')} file${failed ? `; ${failed} file bị lỗi, xem chi tiết bên dưới` : ''}. ZIP kèm báo cáo kết quả.`,failed>0);
  }catch(error){message(error.message||'Kết nối bị gián đoạn. Hãy thử lại.',true);}finally{setBusy(false);}
};
