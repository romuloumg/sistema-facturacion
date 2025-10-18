// Toggle claro/oscuro con persistencia
const saved = localStorage.getItem('theme') || 'dark';
if (saved === 'light') document.documentElement.classList.add('theme-light');

document.getElementById('themeToggle')?.addEventListener('click', () => {
  document.documentElement.classList.toggle('theme-light');
  localStorage.setItem(
    'theme',
    document.documentElement.classList.contains('theme-light') ? 'light' : 'dark'
  );
});
