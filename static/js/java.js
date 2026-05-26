/* Morphing Dropdown Logic */
const nav = document.getElementById('navbar');
const menuContents = document.querySelectorAll('.menu-content');
let closeTimeout;

function openMenu(event,menuId) {

  clearTimeout(closeTimeout); 
  

  menuContents.forEach(el => el.style.display = 'none');
  

  document.querySelectorAll('.nav-links a').forEach(el => el.parentElement.classList.remove('active-link'));
  

  const targetMenu = document.getElementById('menu-' + menuId);
  if (targetMenu) {
    targetMenu.style.display = 'block';
    nav.classList.add('expanded');
    

    event.target.closest('li').classList.add('active-link');
  }
}

function closeMenu() {

  closeTimeout = setTimeout(() => {
    nav.classList.remove('expanded');
    document.querySelectorAll('.nav-links a').forEach(el => el.parentElement.classList.remove('active-link'));
  }, 150);
}


document.addEventListener("DOMContentLoaded", () => {
  const track = document.getElementById("marqueeTrack");

  // auto copy
  track.innerHTML += track.innerHTML;
});