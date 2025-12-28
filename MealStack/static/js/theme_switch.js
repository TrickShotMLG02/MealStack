function getCurrentTheme() {
    return localStorage.getItem('theme') || 'light';
}

function applyTheme(theme) {
    const themeLink = document.getElementById('theme-link');
    if (!themeLink) return;

    themeLink.href = `/static/css/themes/theme_${theme}.css`;
    localStorage.setItem('theme', theme);
}

// Toggle between light and dark
function toggleTheme() {
    const current = getCurrentTheme();
    const next = current === 'light' ? 'dark' : 'light';
    applyTheme(next);
}

// Initialize on page load
function initTheme() {
    applyTheme(getCurrentTheme());

    const toggleBtn = document.getElementById('theme-toggle');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleTheme);
    }
}

document.addEventListener('DOMContentLoaded', initTheme);