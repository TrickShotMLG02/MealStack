function initRecipeDetailPage() {
    const article = document.querySelector('.recipe-detail');
    const toggle = document.querySelector('[data-cook-toggle]');

    if (!article || !toggle) {
        return;
    }

    const storageKey = 'recipe-cook-mode';

    function setMode(enabled) {
        article.classList.toggle('recipe-detail--cook-mode', enabled);
        toggle.setAttribute('aria-pressed', String(enabled));
        toggle.textContent = enabled ? toggle.dataset.labelOn : toggle.dataset.labelOff;
        localStorage.setItem(storageKey, enabled ? '1' : '0');
    }

    const saved = localStorage.getItem(storageKey) === '1';
    setMode(saved);

    toggle.addEventListener('click', () => {
        setMode(!article.classList.contains('recipe-detail--cook-mode'));
    });
}

document.addEventListener('DOMContentLoaded', initRecipeDetailPage);
