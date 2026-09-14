(function () {
    "use strict";

    function initializePreview() {
        const input = document.getElementById("id_image_url");
        const preview = document.querySelector("[data-oidc-image-preview]");
        const image = document.querySelector("[data-oidc-image-preview-image]");
        const empty = document.querySelector("[data-oidc-image-preview-empty]");

        if (!input || !preview || !image || !empty) {
            return;
        }

        const update = function () {
            const url = input.value.trim();
            image.classList.add("is-hidden");
            empty.classList.remove("is-hidden");

            if (!url) {
                image.removeAttribute("src");
                return;
            }

            image.onload = function () {
                image.classList.remove("is-hidden");
                empty.classList.add("is-hidden");
            };
            image.onerror = function () {
                image.classList.add("is-hidden");
                empty.classList.remove("is-hidden");
            };
            image.src = url;
        };

        input.addEventListener("input", update);
        update();
    }

    document.addEventListener("DOMContentLoaded", initializePreview);
})();
