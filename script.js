const lightbox = document.querySelector('.lightbox');
const lightboxImage = document.querySelector('.lightbox img');
const galleryTrigger = document.querySelector('.gallery-trigger');
const closeButton = document.querySelector('.lightbox button');

if (galleryTrigger && lightbox && lightboxImage && closeButton) {
  const openLightbox = () => {
    lightboxImage.src = galleryTrigger.src;
    lightboxImage.alt = galleryTrigger.alt;
    lightbox.classList.add('open');
    document.body.style.overflow = 'hidden';
  };

  const closeLightbox = () => {
    lightbox.classList.remove('open');
    document.body.style.overflow = '';
  };

  galleryTrigger.addEventListener('click', openLightbox);
  closeButton.addEventListener('click', closeLightbox);
  lightbox.addEventListener('click', (event) => {
    if (event.target === lightbox) {
      closeLightbox();
    }
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      closeLightbox();
    }
  });
}
