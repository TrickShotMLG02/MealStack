function initCarousel(carouselContainer) {
    const track = carouselContainer.querySelector('.carousel-track');
    const slides = carouselContainer.querySelectorAll('.carousel-slide');
    const dots = carouselContainer.querySelectorAll('.dot');
    let slideIndex = 0;

    function update() {
        const offset = -slideIndex * 100;
        track.style.transform = `translateX(${offset}%)`;
        dots.forEach((dot, i) => dot.classList.toggle('active', i === slideIndex));
    }

    carouselContainer.changeSlide = function(direction) {
        slideIndex += direction;
        if(slideIndex >= slides.length) slideIndex = 0;
        if(slideIndex < 0) slideIndex = slides.length - 1;
        update();
    };

    carouselContainer.currentSlide = function(index) {
        slideIndex = index;
        update();
    };

    // Initialize
    update();

    return carouselContainer;
}

// Hook arrows and dots
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.carousel-container').forEach(container => {
        const carousel = initCarousel(container);

        container.querySelector('.carousel-prev').onclick = () => carousel.changeSlide(-1);
        container.querySelector('.carousel-next').onclick = () => carousel.changeSlide(1);
        container.querySelectorAll('.dot').forEach((dot, i) => {
            dot.onclick = () => carousel.currentSlide(i);
        });
    });
});