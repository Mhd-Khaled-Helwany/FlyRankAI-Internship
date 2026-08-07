const lightbox = document.querySelector('.lightbox');
const lightboxImage = document.querySelector('.lightbox img');
const galleryTrigger = document.querySelector('.gallery-trigger');
const closeButton = document.querySelector('.lightbox button');
const emailTrigger = document.querySelector('.email-trigger');
const emailModal = document.querySelector('.email-modal');
const emailModalClose = document.querySelector('.email-modal-close');
const copyEmailButton = document.querySelector('.copy-email-btn');
const emailStatus = document.querySelector('.email-status');
const emailAddress = 'MKhelwani@gmail.com';

const closeLightbox = () => {
  if (lightbox) {
    lightbox.classList.remove('open');
  }
  document.body.style.overflow = '';
};

const closeEmailModal = () => {
  if (emailModal) {
    emailModal.classList.remove('open');
    emailModal.setAttribute('aria-hidden', 'true');
  }
  document.body.style.overflow = '';
};

if (galleryTrigger && lightbox && lightboxImage && closeButton) {
  const openLightbox = () => {
    lightboxImage.src = galleryTrigger.src;
    lightboxImage.alt = galleryTrigger.alt;
    lightbox.classList.add('open');
    lightbox.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
  };

  galleryTrigger.addEventListener('click', openLightbox);
  closeButton.addEventListener('click', closeLightbox);
  lightbox.addEventListener('click', (event) => {
    if (event.target === lightbox) {
      closeLightbox();
    }
  });
}

if (emailTrigger && emailModal && emailModalClose && copyEmailButton) {
  emailTrigger.addEventListener('click', () => {
    emailModal.classList.add('open');
    emailModal.setAttribute('aria-hidden', 'false');
    if (emailStatus) {
      emailStatus.textContent = '';
    }
    document.body.style.overflow = 'hidden';
  });

  emailModalClose.addEventListener('click', closeEmailModal);
  emailModal.addEventListener('click', (event) => {
    if (event.target === emailModal) {
      closeEmailModal();
    }
  });

  copyEmailButton.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(emailAddress);
      if (emailStatus) {
        emailStatus.textContent = 'Email copied to clipboard.';
      }
    } catch (error) {
      if (emailStatus) {
        emailStatus.textContent = 'Copy failed. Please select the email manually.';
      }
    }
  });
}

document.querySelectorAll('.accordion-toggle').forEach((toggle) => {
  const content = toggle.nextElementSibling;

  if (!(content instanceof HTMLElement)) {
    return;
  }

  toggle.addEventListener('click', () => {
    const expanded = toggle.getAttribute('aria-expanded') === 'true';
    toggle.setAttribute('aria-expanded', String(!expanded));
    content.classList.toggle('open', !expanded);

    if (!expanded) {
      content.style.maxHeight = content.scrollHeight + 'px';
    } else {
      content.style.maxHeight = '0';
    }
  });
});

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') {
    closeLightbox();
    closeEmailModal();
  }
});
