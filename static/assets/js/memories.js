// ─── LIGHTBOX ───────────────────────────────────────

let currentPhotos = [];
let currentIndex  = 0;

function openLightbox(url, albumName, type) {

    const content = document.getElementById('lightboxContent');

    // clear previous media
    content.innerHTML = '';

    if (type === 'video') {

        const vid       = document.createElement('video');
        vid.src         = url;
        vid.controls    = true;
        vid.autoplay    = true;
        vid.style.maxWidth     = '90vw';
        vid.style.maxHeight    = '82vh';
        vid.style.borderRadius = '10px';
        vid.style.boxShadow    = '0 8px 40px rgba(0,0,0,0.5)';
        content.appendChild(vid);

    } else {

        const img = document.createElement('img');
        img.id    = 'lightboxImg';
        img.src   = url;
        content.appendChild(img);

    }

    const cap           = document.createElement('div');
    cap.className       = 'lightbox-caption';
    cap.id              = 'lightboxCaption';
    cap.textContent     = albumName;
    content.appendChild(cap);

    // build navigation list from all visible items
    currentPhotos = Array.from(
        document.querySelectorAll('.photo-item')
    ).map(el => ({
        url : el.querySelector('img, video')?.src || '',
        type: el.querySelector('video') ? 'video' : 'image',
        name: el.closest('.album-card')
                ?.querySelector('.album-title')
                ?.textContent?.trim() || albumName
    }));

    currentIndex = currentPhotos.findIndex(p => p.url === url);

    document.getElementById('lightboxOverlay').style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

function closeLightbox() {

    // pause any playing video
    const vid = document.querySelector('#lightboxContent video');
    if (vid) vid.pause();

    document.getElementById('lightboxOverlay').style.display = 'none';
    document.body.style.overflow = '';
}

function prevPhoto() {
    if (!currentPhotos.length) return;
    currentIndex = (currentIndex - 1 + currentPhotos.length) % currentPhotos.length;
    const p = currentPhotos[currentIndex];
    openLightbox(p.url, p.name, p.type);
}

function nextPhoto() {
    if (!currentPhotos.length) return;
    currentIndex = (currentIndex + 1) % currentPhotos.length;
    const p = currentPhotos[currentIndex];
    openLightbox(p.url, p.name, p.type);
}

document.addEventListener('keydown', e => {
    const overlay = document.getElementById('lightboxOverlay');
    if (overlay.style.display !== 'flex') return;
    if (e.key === 'Escape')     closeLightbox();
    if (e.key === 'ArrowLeft')  prevPhoto();
    if (e.key === 'ArrowRight') nextPhoto();
});

// ─── CREATE ALBUM ────────────────────────────────────

function createAlbum() {

    const input = document.getElementById('newAlbumName');
    const name  = input.value.trim();

    if (!name) {
        input.focus();
        return;
    }

    fetch('/memories/create-album', {
        method : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body   : JSON.stringify({ name })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            input.value = '';
            location.reload();
        } else {
            alert('Tạo album thất bại');
        }
    });
}

document.getElementById('newAlbumName')?.addEventListener('keydown', e => {
    if (e.key === 'Enter') createAlbum();
});

// ─── UPLOAD PHOTOS / VIDEOS ──────────────────────────

function uploadPhotos(input, albumId) {

    const files = Array.from(input.files);
    if (!files.length) return;

    const toast     = document.getElementById('uploadToast');
    const toastBar  = document.getElementById('toastBar');
    const toastText = document.getElementById('toastText');

    toast.style.display = 'block';

    const uploadNext = (i) => {

        if (i >= files.length) {
            toastText.textContent = '✅ Tải lên hoàn tất!';
            toastBar.style.width  = '100%';
            setTimeout(() => {
                toast.style.display = 'none';
                location.reload();
            }, 1000);
            return;
        }

        const file     = files[i];
        const isVideo  = file.type.startsWith('video');
        const label    = isVideo ? 'video' : 'ảnh';
        const formData = new FormData();

        formData.append('image',    file);
        formData.append('album_id', albumId);

        toastText.textContent = `Đang tải ${label} ${i + 1}/${files.length}...`;
        toastBar.style.width  = `${Math.round((i / files.length) * 100)}%`;

        fetch('/memories/upload-photo', {
            method: 'POST',
            body  : formData
        })
        .then(r => r.json())
        .then(() => uploadNext(i + 1))
        .catch(() => uploadNext(i + 1));
    };

    uploadNext(0);
}

// ─── DELETE PHOTO / VIDEO ────────────────────────────

function deletePhoto(photoId, albumId, btn) {

    if (!confirm('Xóa mục này?')) return;

    fetch('/memories/delete-photo', {
        method : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body   : JSON.stringify({ photo_id: photoId, album_id: albumId })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) btn.closest('.photo-item').remove();
    });
}

// ─── DELETE ALBUM ────────────────────────────────────

function deleteAlbum(albumId) {

    if (!confirm('Xóa album này và toàn bộ ảnh/video?')) return;

    fetch('/memories/delete-album', {
        method : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body   : JSON.stringify({ album_id: albumId })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) location.reload();
    });
}