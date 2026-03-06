document.addEventListener('DOMContentLoaded', () => {
    // Custom Cursor
    const cursorDot = document.querySelector('.cursor-dot');
    const cursorOutline = document.querySelector('.cursor-outline');

    if (cursorDot && cursorOutline) {
        window.addEventListener('mousemove', (e) => {
            const posX = e.clientX;
            const posY = e.clientY;

            cursorDot.style.left = `${posX}px`;
            cursorDot.style.top = `${posY}px`;

            cursorOutline.animate({
                left: `${posX}px`,
                top: `${posY}px`
            }, { duration: 400, fill: "forwards" });
        });
    }

    // Smooth Scroll
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // Ken Burns Video Slideshow
    const slideshowContainer = document.querySelector('.slideshow-mini');
    if (slideshowContainer) {
        const images = [
            './assets/images/promo_0.jpg',
            './assets/images/promo_1.jpg',
            './assets/images/promo_2.jpg',
            './assets/images/promo_3.jpg',
            './assets/images/promo_4.jpg'
        ];

        let currentIndex = 0;

        // Create image elements
        images.forEach((src, index) => {
            const img = document.createElement('div');
            img.className = 'slide-bg';
            img.style.backgroundImage = `url('${src}')`;
            if (index === 0) img.classList.add('active');
            slideshowContainer.appendChild(img);
        });

        // Loop
        const slides = document.querySelectorAll('.slide-bg');
        setInterval(() => {
            slides[currentIndex].classList.remove('active');

            currentIndex = (currentIndex + 1) % slides.length;

            slides[currentIndex].classList.add('active');
        }, 5000); // Change every 5 seconds
    }
});
