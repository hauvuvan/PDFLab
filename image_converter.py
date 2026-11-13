"""Local PDF/image conversion with bounded raster work."""
import io
import warnings
import zipfile
import fitz
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_PIXELS = 25_000_000


def pdf_to_images(data, fmt='png', dpi=150):
    if fmt not in ('png', 'jpg') or dpi not in (72, 150, 200, 300):
        raise ValueError('Định dạng hoặc độ phân giải không hợp lệ.')
    try:
        doc = fitz.open(stream=data, filetype='pdf')
    except Exception:
        raise ValueError('Không đọc được PDF.')
    with doc:
        if doc.needs_pass or not 1 <= len(doc) <= 200:
            raise ValueError('PDF cần mở khóa và có từ 1 đến 200 trang.')
        pixels = [(page.rect.width * dpi / 72) * (page.rect.height * dpi / 72) for page in doc]
        if any(n > MAX_PIXELS for n in pixels) or sum(pixels) > 200_000_000:
            raise ValueError('PDF quá lớn để xuất ở độ phân giải này. Hãy giảm DPI hoặc chia nhỏ PDF.')
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
            for i, page in enumerate(doc):
                pix = page.get_pixmap(dpi=dpi, colorspace=fitz.csRGB, alpha=False)
                archive.writestr(f'trang-{i + 1:04d}.{fmt}', pix.tobytes('jpeg' if fmt == 'jpg' else 'png'))
        return output.getvalue()


def images_to_pdf(files, paper='a4'):
    if paper not in ('a4', 'image') or not 1 <= len(files) <= 100:
        raise ValueError('Chọn từ 1 đến 100 ảnh và khổ giấy hợp lệ.')
    with fitz.open() as doc:
        total = 0
        for name, data in files:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter('error', Image.DecompressionBombWarning)
                    with Image.open(io.BytesIO(data)) as original:
                        if original.format not in ('PNG', 'JPEG', 'WEBP'):
                            raise ValueError('Chỉ hỗ trợ ảnh PNG, JPG và WebP.')
                        total += original.width * original.height
                        if original.width * original.height > MAX_PIXELS or total > 200_000_000:
                            raise ValueError('Ảnh quá lớn hoặc tổng số điểm ảnh vượt giới hạn. Hãy chia nhỏ lượt ghép.')
                        image = ImageOps.exif_transpose(original).convert('RGBA')
                        background = Image.new('RGB', image.size, 'white')
                        background.paste(image, mask=image.getchannel('A'))
                        encoded = io.BytesIO()
                        background.save(encoded, format='JPEG', quality=95)
                        width, height = image.size
            except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning):
                raise ValueError('Không đọc được ảnh hoặc ảnh vượt giới hạn an toàn.')
            if paper == 'a4':
                w, h = (842, 595) if width > height else (595, 842)
                page = doc.new_page(width=w, height=h)
                rect = fitz.Rect(20, 20, w - 20, h - 20)
            else:
                w, h = width * 72 / 150, height * 72 / 150
                page = doc.new_page(width=w, height=h)
                rect = page.rect
            page.insert_image(rect, stream=encoded.getvalue(), keep_proportion=True)
        return doc.tobytes(garbage=4, deflate=True)
