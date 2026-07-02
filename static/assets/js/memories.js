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
