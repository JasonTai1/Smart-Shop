// ===== Help Centre Scripts =====

// Toggle FAQ answer open/close
function toggleFAQ(el) {
  const answer = el.nextElementSibling;
  const arrow = el.querySelector('.faq-arrow');

  if (answer.classList.contains('open')) {
    answer.classList.remove('open');
    arrow.textContent = '+';
  } else {
    answer.classList.add('open');
    arrow.textContent = '−';
  }
}

// Live search filter across FAQ items and sections
function filterFAQ() {
  const term = document.getElementById('helpSearch').value.toLowerCase();

  document.querySelectorAll('.faq-item').forEach(item => {
    const text = item.innerText.toLowerCase();
    item.style.display = text.includes(term) ? '' : 'none';
  });

  // Hide a whole section if none of its FAQ items match
  document.querySelectorAll('.help-section').forEach(section => {
    const items = section.querySelectorAll('.faq-item');
    if (items.length === 0) return;

    const anyVisible = Array.from(items).some(i => i.style.display !== 'none');
    section.style.display = anyVisible ? '' : 'none';
  });
}

// Highlight active sidebar link based on scroll position
function setupScrollSpy() {
  const sections = document.querySelectorAll('.help-section[id]');
  const links = document.querySelectorAll('.help-nav-link');

  window.addEventListener('scroll', () => {
    let current = '';

    sections.forEach(section => {
      const rect = section.getBoundingClientRect();
      if (rect.top <= 120 && rect.bottom >= 120) {
        current = section.getAttribute('id');
      }
    });

    links.forEach(link => {
      link.classList.remove('active');
      if (link.getAttribute('href') === '#' + current) {
        link.classList.add('active');
      }
    });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('helpSearch');
  if (searchInput) {
    searchInput.addEventListener('input', filterFAQ);
  }
  setupScrollSpy();
});

function openLiveChat() {
    alert("Live Chat is currently unavailable. Please email us at smartshopmalaysia3@gmail.com");
}