(() => {
  const $ = s => document.querySelector(s);
  const mode = $('.image-tool').dataset.mode, single = mode === 'pdf-to-images';
  let files = [], busy = false, url;
  function message(text, error = false) { $('#image-status').textContent = text; $('#image-status').classList.toggle('error', error); }
  function invalidate() { if(url) URL.revokeObjectURL(url); url = null; $('#image-download').hidden = true; }
  function render() {
    $('#image-list').replaceChildren();
    files.forEach((file, i) => {
      const row = document.createElement('div'); row.className = 'file-row';
      const name = document.createElement('span'); name.className = 'name'; name.textContent = `${i + 1}. ${file.name}`; name.title = file.name; row.append(name);
      function button(text, label, disabled, action) { const b = document.createElement('button'); b.type = 'button'; b.textContent = text; b.setAttribute('aria-label', label + ' ' + file.name); b.disabled = busy || disabled; b.onclick = () => { action(); invalidate(); render(); }; row.append(b); }
      if(!single) { button('↑', 'Đưa lên', i === 0, () => {[files[i-1], files[i]] = [files[i], files[i-1]];}); button('↓', 'Đưa xuống', i === files.length-1, () => {[files[i+1], files[i]] = [files[i], files[i+1]];}); }
      button('×', 'Bỏ', false, () => files.splice(i, 1)); $('#image-list').append(row);
    });
    $('#image-start').disabled = busy || !files.length;
    $('#image-form').querySelectorAll('select,input').forEach(e => e.disabled = busy);
  }
  function add(incoming) {
    if(busy) return;
    const next = single ? [...incoming] : [...files, ...incoming];
    if(!next.length) return;
    if(next.length > (single ? 1 : 100)) return message(single ? 'Chọn một PDF mỗi lượt.' : 'Tối đa 100 ảnh mỗi lượt.', true);
    if(next.some(f => !(single ? /\.pdf$/i : /\.(png|jpe?g|webp)$/i).test(f.name))) return message('Định dạng file không được hỗ trợ.', true);
    if(next.reduce((n,f) => n + f.size, 0) > 195*1024*1024) return message('Tổng file vượt 195 MB.', true);
    files = next; invalidate(); render(); message(`Đã chọn ${files.length} file.`);
  }
  $('#image-files').onchange = e => { add(e.target.files); e.target.value = ''; };
  const drop = $('#image-drop');
  ['dragover','drop'].forEach(event => drop.addEventListener(event, e => { e.preventDefault(); if(event === 'drop') add(e.dataTransfer.files); }));
  $('#image-form').onchange = e => {if(e.target.tagName === 'SELECT') invalidate();};
  $('#image-form').onsubmit = async e => {
    e.preventDefault(); if(busy || !files.length) return;
    const data = new FormData($('#image-form')); files.forEach(f => data.append(single ? 'pdf' : 'images', f));
    invalidate(); busy = true; render(); message('Đang tải lên và xử lý, vui lòng giữ trang mở…');
    try {
      const response = await fetch('/api/' + mode, {method:'POST', body:data});
      if(!response.ok) {const body = await response.json(); throw new Error(body.error || 'Không chuyển đổi được file.');}
      url = URL.createObjectURL(await response.blob()); const link = $('#image-download'); link.href = url; link.download = single ? 'pdf-sang-anh.zip' : 'anh-da-ghep.pdf'; link.hidden = false; message('Đã hoàn tất. Nhấn Tải kết quả để lưu file.');
    } catch(error) { message(error.message, true); } finally { busy = false; render(); }
  };
})();
