function initCarousel(carouselContainer) {
    const track = carouselContainer.querySelector('.carousel-track');
    const slides = carouselContainer.querySelectorAll('.carousel-slide');
    const dots = carouselContainer.querySelectorAll('.dot');
    let slideIndex = 0;
    let isAnimating = false;
    let animationTimer = null;

    if (!track || !slides.length) {
        return null;
    }

    function finishAnimation() {
        isAnimating = false;
        if (animationTimer) {
            window.clearTimeout(animationTimer);
            animationTimer = null;
        }
    }

    function update() {
        slideIndex = Math.max(0, Math.min(slideIndex, slides.length - 1));
        const offset = -slideIndex * 100;
        track.style.transform = `translateX(${offset}%)`;
        dots.forEach((dot, i) => dot.classList.toggle('active', i === slideIndex));
    }

    carouselContainer.changeSlide = function(direction) {
        if (isAnimating || slides.length < 2) {
            return;
        }

        isAnimating = true;
        slideIndex += direction;
        if(slideIndex >= slides.length) slideIndex = 0;
        if(slideIndex < 0) slideIndex = slides.length - 1;
        update();
        animationTimer = window.setTimeout(finishAnimation, 520);
    };

    carouselContainer.currentSlide = function(index) {
        if (isAnimating || index === slideIndex) {
            return;
        }

        isAnimating = true;
        slideIndex = index;
        update();
        animationTimer = window.setTimeout(finishAnimation, 520);
    };

    track.addEventListener('transitionend', (event) => {
        if (event.target === track && event.propertyName === 'transform') {
            finishAnimation();
        }
    });

    // Initialize
    update();

    return carouselContainer;
}

// Hook arrows and dots
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.carousel-container').forEach(container => {
        const carousel = initCarousel(container);
        if (!carousel) {
            return;
        }

        const prevButton = container.querySelector('.carousel-prev');
        const nextButton = container.querySelector('.carousel-next');

        if (prevButton) {
            prevButton.onclick = () => carousel.changeSlide(-1);
        }

        if (nextButton) {
            nextButton.onclick = () => carousel.changeSlide(1);
        }

        container.querySelectorAll('.dot').forEach((dot, i) => {
            dot.onclick = () => carousel.currentSlide(i);
        });
    });
});
