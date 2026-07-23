function initHeaderSearch() {
    const form = document.querySelector('[data-search-form]');
    if (!form) {
        return;
    }

    const input = form.querySelector('input[name="q"]');
    const panel = form.querySelector('[data-search-suggestions]');
    const endpoint = form.dataset.suggestionsUrl;
    if (!input || !panel || !endpoint) {
        return;
    }

    let debounceTimer = null;
    let activeRequest = null;
    let hideTimer = null;

    function setExpanded(expanded) {
        form.setAttribute('aria-expanded', String(expanded));
    }

    function hideSuggestions() {
        if (hideTimer) {
            window.clearTimeout(hideTimer);
            hideTimer = null;
        }

        if (activeRequest) {
            activeRequest.abort();
            activeRequest = null;
        }

        panel.replaceChildren();
        panel.hidden = true;
        setExpanded(false);
    }

    function showSuggestions(items) {
        panel.replaceChildren();

        if (!items.length) {
            hideSuggestions();
            return;
        }

        items.forEach((item) => {
            const link = document.createElement('a');
            link.className = 'header-search__suggestion';
            link.href = item.href;
            link.setAttribute('role', 'option');
            link.setAttribute('aria-label', `${item.kind_label}: ${item.label}`);

            const kind = document.createElement('span');
            kind.className = 'header-search__suggestion-kind';
            kind.textContent = item.kind_label;

            const label = document.createElement('span');
            label.className = 'header-search__suggestion-label';
            label.textContent = item.label;

            link.append(kind, label);
            panel.append(link);
        });

        panel.hidden = false;
        setExpanded(true);
    }

    async function fetchSuggestions(query) {
        const normalized = query.trim();
        if (normalized.length < 2) {
            hideSuggestions();
            return;
        }

        if (activeRequest) {
            activeRequest.abort();
        }

        activeRequest = new AbortController();
        const url = new URL(endpoint, window.location.origin);
        url.searchParams.set('q', normalized);

        try {
            const response = await fetch(url.toString(), {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
                signal: activeRequest.signal,
            });

            if (!response.ok) {
                hideSuggestions();
                return;
            }

            const payload = await response.json();
            const items = Array.isArray(payload.suggestions) ? payload.suggestions : [];

            if (input.value.trim() !== normalized) {
                return;
            }

            showSuggestions(items);
        } catch (error) {
            if (error.name !== 'AbortError') {
                hideSuggestions();
            }
        }
    }

    function scheduleFetch() {
        if (debounceTimer) {
            window.clearTimeout(debounceTimer);
        }

        debounceTimer = window.setTimeout(() => {
            fetchSuggestions(input.value);
        }, 180);
    }

    input.addEventListener('input', scheduleFetch);
    input.addEventListener('focus', scheduleFetch);
    input.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            hideSuggestions();
        }
    });

    form.addEventListener('focusout', (event) => {
        if (form.contains(event.relatedTarget)) {
            return;
        }

        hideTimer = window.setTimeout(() => {
            hideSuggestions();
        }, 120);
    });

    document.addEventListener('click', (event) => {
        if (!form.contains(event.target)) {
            hideSuggestions();
        }
    });

    if (input.value.trim()) {
        scheduleFetch();
    }
}

document.addEventListener('DOMContentLoaded', initHeaderSearch);
