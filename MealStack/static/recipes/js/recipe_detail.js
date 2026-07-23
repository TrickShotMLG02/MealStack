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
    const url = new URL(window.location.href);
    const servingsDisplays = document.querySelectorAll('[data-servings-display]');
    const selectedServingsSummary = document.querySelector('[data-selected-servings-summary]');
    const selectedServingsNote = document.querySelector('[data-selected-servings-note]');
    const ingredientAmounts = document.querySelectorAll('[data-ingredient-quantity]');
    const nutritionValues = document.querySelectorAll('[data-nutrition-metric]');

    function parseNumeric(value) {
        if (typeof value === 'number') {
            return value;
        }

        if (typeof value !== 'string') {
            return 0;
        }

        const normalized = value.trim().replace(/\s+/g, '').replace(',', '.');
        const parsed = Number(normalized);
        return Number.isFinite(parsed) ? parsed : 0;
    }

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

        const pdfUrl = new URL(pdfLink.getAttribute('href'), window.location.href);
        pdfUrl.searchParams.set('servings', String(servings));
        pdfLink.href = pdfUrl.toString();
    }

    function updateNutrition(servings) {
        nutritionValues.forEach((element) => {
            const perServingElement = element.querySelector('[data-nutrition-per-serving]');
            const totalElement = element.querySelector('[data-nutrition-total]');
            const perServing = parseNumeric(perServingElement?.textContent || '0');
            const total = perServing * servings;
            if (perServingElement) {
                perServingElement.textContent = nutritionFormatter.format(perServing);
            }

            if (totalElement) {
                totalElement.textContent = nutritionFormatter.format(total);
            }
        });
    }

    function updateIngredients(servings) {
        ingredientAmounts.forEach((element) => {
            const baseQuantity = parseNumeric(element.dataset.baseQuantity);
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

        url.searchParams.set('servings', String(servings));
        history.replaceState({}, '', url.toString());
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
