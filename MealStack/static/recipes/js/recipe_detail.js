function initRecipeDetailPage() {
    const article = document.querySelector('.recipe-detail');
    const toggle = document.querySelector('[data-cook-toggle]');
    const servingsControl = document.querySelector('[data-servings-control]');
    const servingsInput = document.querySelector('[data-servings-input]');
    const servingsDecrease = document.querySelector('[data-servings-decrease]');
    const servingsIncrease = document.querySelector('[data-servings-increase]');
    const pdfLink = document.querySelector('[data-pdf-link]');
    const shareButton = document.querySelector('[data-share-button]');

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
    let shareLabelResetTimer = null;

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

    function gcd(a, b) {
        let x = Math.abs(a);
        let y = Math.abs(b);

        while (y) {
            const temp = y;
            y = x % y;
            x = temp;
        }

        return x || 1;
    }

    function formatFractionValue(value) {
        const sign = value < 0 ? '-' : '';
        const absolute = Math.abs(value);
        const whole = Math.floor(absolute + 1e-9);
        const remainder = absolute - whole;

        if (remainder < 0.02) {
            return `${sign}${whole}`;
        }

        const denominators = [2, 3, 4, 5, 6, 8, 10, 12, 16];
        let best = null;

        denominators.forEach((denominator) => {
            const numerator = Math.round(remainder * denominator);
            if (numerator === 0 || numerator === denominator) {
                return;
            }

            const approximation = numerator / denominator;
            const error = Math.abs(approximation - remainder);
            if (!best || error < best.error) {
                best = { numerator, denominator, error };
            }
        });

        if (!best || best.error > 0.03) {
            return `${sign}${quantityFormatter.format(value)}`;
        }

        const divisor = gcd(best.numerator, best.denominator);
        const numerator = best.numerator / divisor;
        const denominator = best.denominator / divisor;
        const fraction = `${numerator}/${denominator}`;

        return whole ? `${sign}${whole} ${fraction}` : `${sign}${fraction}`;
    }

    function formatIngredientQuantity(value, unit) {
        const formatted = formatFractionValue(value);
        return unit ? `${formatted} ${unit}` : formatted;
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
            const perServing = parseNumeric(element.dataset.perServing);
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
            element.textContent = formatIngredientQuantity(scaled, unit);
        });
    }

    function resetShareButtonLabel() {
        if (!shareButton) {
            return;
        }

        if (shareLabelResetTimer) {
            window.clearTimeout(shareLabelResetTimer);
            shareLabelResetTimer = null;
        }

        shareButton.textContent = shareButton.dataset.labelDefault || shareButton.textContent;
    }

    function showShareCopied() {
        if (!shareButton) {
            return;
        }

        shareButton.textContent = shareButton.dataset.labelCopied || shareButton.textContent;
        if (shareLabelResetTimer) {
            window.clearTimeout(shareLabelResetTimer);
        }

        shareLabelResetTimer = window.setTimeout(() => {
            resetShareButtonLabel();
        }, 1800);
    }

    async function shareRecipe() {
        const shareData = {
            title: document.title,
            text: document.title,
            url: url.toString(),
        };

        if (navigator.share) {
            await navigator.share(shareData);
            return;
        }

        if (navigator.clipboard && navigator.clipboard.writeText) {
            await navigator.clipboard.writeText(shareData.url);
            showShareCopied();
            return;
        }

        showShareCopied();
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

    if (shareButton) {
        shareButton.addEventListener('click', () => {
            shareRecipe().catch(() => {
                resetShareButtonLabel();
            });
        });
    }
}

document.addEventListener('DOMContentLoaded', initRecipeDetailPage);
