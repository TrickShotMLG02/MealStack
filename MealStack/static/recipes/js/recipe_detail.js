function initRecipeDetailPage() {
    const article = document.querySelector('.recipe-detail');
    const toggle = document.querySelector('[data-cook-toggle]');
    const servingsControl = document.querySelector('[data-servings-control]');
    const servingsInput = document.querySelector('[data-servings-input]');
    const servingsDecrease = document.querySelector('[data-servings-decrease]');
    const servingsIncrease = document.querySelector('[data-servings-increase]');
    const pdfLink = document.querySelector('[data-pdf-link]');

    if (!article || !toggle) {
        return;
    }

    const storageKey = 'recipe-cook-mode';
    const baseServings = Number(article.dataset.baseServings || servingsInput?.value || 1) || 1;
    const locale = document.documentElement.lang || navigator.language || 'en';
    const servingsFormatter = new Intl.NumberFormat(locale, { maximumFractionDigits: 0 });
    const quantityFormatter = new Intl.NumberFormat(locale, {
        maximumFractionDigits: 2,
        minimumFractionDigits: 0,
        useGrouping: false,
    });
    const nutritionFormatter = new Intl.NumberFormat(locale, {
        maximumFractionDigits: 0,
        minimumFractionDigits: 0,
        useGrouping: false,
    });
    const servingsDisplays = document.querySelectorAll('[data-servings-display]');
    const selectedServingsSummary = document.querySelector('[data-selected-servings-summary]');
    const selectedServingsNote = document.querySelector('[data-selected-servings-note]');
    const ingredientAmounts = document.querySelectorAll('[data-ingredient-quantity]');
    const nutritionValues = document.querySelectorAll('[data-nutrition-value]');

    function clampServings(value) {
        const parsed = Number(value);
        if (!Number.isFinite(parsed)) {
            return baseServings;
        }

        return Math.max(1, Math.round(parsed));
    }

    function setPdfHref(servings) {
        if (!pdfLink) {
            return;
        }

        const url = new URL(pdfLink.getAttribute('href'), window.location.href);
        url.searchParams.set('servings', String(servings));
        pdfLink.href = url.toString();
    }

    function updateNutrition(servings) {
        nutritionValues.forEach((element) => {
            const perServing = Number(element.dataset.perServing || 0);
            const total = perServing * servings;
            const suffix = element.dataset.unit || '';
            element.textContent = `${nutritionFormatter.format(total)}${suffix}`;
        });
    }

    function updateIngredients(servings) {
        ingredientAmounts.forEach((element) => {
            const baseQuantity = Number(element.dataset.baseQuantity || 0);
            const unit = element.dataset.unit || '';
            const scaled = (baseQuantity * servings) / baseServings;
            element.textContent = `${quantityFormatter.format(scaled)}${unit ? ` ${unit}` : ''}`;
        });
    }

    function updateServingsDisplays(servings) {
        servingsDisplays.forEach((element) => {
            element.textContent = servingsFormatter.format(servings);
        });

        if (selectedServingsSummary) {
            selectedServingsSummary.textContent = servingsFormatter.format(servings);
        }

        if (selectedServingsNote) {
            selectedServingsNote.textContent = servingsFormatter.format(servings);
        }
    }

    function setServings(value) {
        const servings = clampServings(value);
        if (servingsInput) {
            servingsInput.value = String(servings);
        }

        updateServingsDisplays(servings);
        updateIngredients(servings);
        updateNutrition(servings);
        setPdfHref(servings);
    }

    function setMode(enabled) {
        article.classList.toggle('recipe-detail--cook-mode', enabled);
        toggle.setAttribute('aria-pressed', String(enabled));
        toggle.textContent = enabled ? toggle.dataset.labelOn : toggle.dataset.labelOff;
        localStorage.setItem(storageKey, enabled ? '1' : '0');
    }

    const saved = localStorage.getItem(storageKey) === '1';
    setMode(saved);
    setServings(servingsInput ? servingsInput.value : baseServings);

    if (servingsInput) {
        servingsInput.addEventListener('input', () => {
            setServings(servingsInput.value);
        });

        servingsInput.addEventListener('change', () => {
            setServings(servingsInput.value);
        });
    }

    if (servingsDecrease) {
        servingsDecrease.addEventListener('click', () => {
            setServings(clampServings(Number(servingsInput ? servingsInput.value : baseServings) - 1));
        });
    }

    if (servingsIncrease) {
        servingsIncrease.addEventListener('click', () => {
            setServings(clampServings(Number(servingsInput ? servingsInput.value : baseServings) + 1));
        });
    }

    if (servingsControl) {
        servingsControl.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                setServings(servingsInput ? servingsInput.value : baseServings);
            }
        });
    }

    toggle.addEventListener('click', () => {
        setMode(!article.classList.contains('recipe-detail--cook-mode'));
    });
}

document.addEventListener('DOMContentLoaded', initRecipeDetailPage);
