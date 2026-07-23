function initHeaderMenu() {
    const toggle = document.querySelector('[data-header-menu-toggle]');
    const menu = document.querySelector('[data-header-menu]');
    if (!toggle || !menu) {
        return;
    }

    const desktopQuery = window.matchMedia('(min-width: 981px)');

    function setOpen(open) {
        menu.classList.toggle('is-open', open);
        toggle.setAttribute('aria-expanded', String(open));
    }

    toggle.addEventListener('click', () => {
        setOpen(!menu.classList.contains('is-open'));
    });

    document.addEventListener('click', (event) => {
        if (!menu.classList.contains('is-open')) {
            return;
        }

        if (menu.contains(event.target) || toggle.contains(event.target)) {
            return;
        }

        setOpen(false);
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            setOpen(false);
        }
    });

    desktopQuery.addEventListener('change', (event) => {
        if (event.matches) {
            setOpen(false);
        }
    });
}

document.addEventListener('DOMContentLoaded', initHeaderMenu);
