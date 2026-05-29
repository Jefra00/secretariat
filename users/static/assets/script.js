// ============ CARROUSEL HERO ============
let currentHeroSlide = 0;
const heroSlides = document.querySelectorAll('#hero-carousel > div');
const totalHeroSlides = heroSlides.length;
const heroDots = document.querySelectorAll('.hero-dot');
const heroCarousel = document.getElementById('hero-carousel');

function showHeroSlide(index) {
    currentHeroSlide = index;
    const offset = -currentHeroSlide * 100;
    heroCarousel.style.transform = `translateX(${offset}%)`;
    
    // Mise à jour des points indicateurs
    heroDots.forEach((dot, i) => {
        dot.classList.toggle('active', i === currentHeroSlide);
    });
}

// Boutons de navigation Hero
document.getElementById('next-hero')?.addEventListener('click', () => {
    currentHeroSlide = (currentHeroSlide + 1) % totalHeroSlides;
    showHeroSlide(currentHeroSlide);
});

document.getElementById('prev-hero')?.addEventListener('click', () => {
    currentHeroSlide = (currentHeroSlide - 1 + totalHeroSlides) % totalHeroSlides;
    showHeroSlide(currentHeroSlide);
});

// Clics sur les points Hero
heroDots.forEach((dot, i) => {
    dot.addEventListener('click', () => showHeroSlide(i));
});

// Auto-play du carrousel Hero
let heroAutoPlayInterval = setInterval(() => {
    currentHeroSlide = (currentHeroSlide + 1) % totalHeroSlides;
    showHeroSlide(currentHeroSlide);
}, 4000);

// Pause au survol Hero
const heroContainer = document.getElementById('hero-carousel')?.parentElement;
heroContainer?.addEventListener('mouseenter', () => clearInterval(heroAutoPlayInterval));
heroContainer?.addEventListener('mouseleave', () => {
    heroAutoPlayInterval = setInterval(() => {
        currentHeroSlide = (currentHeroSlide + 1) % totalHeroSlides;
        showHeroSlide(currentHeroSlide);
    }, 4000);
});

// ============ CARROUSEL DE TÉMOIGNAGES ============
let currentSlide = 0;
const slides = document.querySelectorAll('#testimonial-carousel > div');
const totalSlides = slides.length;
const dots = document.querySelectorAll('.dot');
const carousel = document.getElementById('testimonial-carousel');

function showSlide(index) {
    currentSlide = index;
    const offset = -currentSlide * 100;
    carousel.style.transform = `translateX(${offset}%)`;
    
    // Mise à jour des points indicateurs
    dots.forEach((dot, i) => {
        dot.classList.toggle('active', i === currentSlide);
    });
}

// Boutons de navigation
document.getElementById('next-testimonial')?.addEventListener('click', () => {
    currentSlide = (currentSlide + 1) % totalSlides;
    showSlide(currentSlide);
});

document.getElementById('prev-testimonial')?.addEventListener('click', () => {
    currentSlide = (currentSlide - 1 + totalSlides) % totalSlides;
    showSlide(currentSlide);
});

// Clics sur les points
dots.forEach((dot, i) => {
    dot.addEventListener('click', () => showSlide(i));
});

// Auto-play du carrousel
let autoPlayInterval = setInterval(() => {
    currentSlide = (currentSlide + 1) % totalSlides;
    showSlide(currentSlide);
}, 5000);

// Pause au survol
const carouselContainer = document.querySelector('.relative');
carouselContainer?.addEventListener('mouseenter', () => clearInterval(autoPlayInterval));
carouselContainer?.addEventListener('mouseleave', () => {
    autoPlayInterval = setInterval(() => {
        currentSlide = (currentSlide + 1) % totalSlides;
        showSlide(currentSlide);
    }, 5000);
});

// ============ ANIMATION DES STATISTIQUES ============
function animateCounter(element, target, duration = 2000) {
    let start = 0;
    const increment = target / (duration / 16);
    
    function updateCounter() {
        start += increment;
        if (start < target) {
            element.textContent = Math.floor(start);
            requestAnimationFrame(updateCounter);
        } else {
            element.textContent = target;
        }
    }
    updateCounter();
}

// Observer pour déclencher l'animation au scroll
const observerOptions = {
    threshold: 0.3,
    rootMargin: '0px'
};

const statsObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting && !entry.target.classList.contains('animated')) {
            entry.target.classList.add('animated');
            const statCards = entry.target.querySelectorAll('.stat-card');
            
            statCards.forEach((card, index) => {
                setTimeout(() => {
                    const targetElement = card.querySelector('[data-target]');
                    const target = parseInt(targetElement.getAttribute('data-target'));
                    animateCounter(targetElement, target);
                }, index * 150);
            });
            
            statsObserver.unobserve(entry.target);
        }
    });
}, observerOptions);

const statsSection = document.querySelector('.bg-gradient-to-br');
if (statsSection) {
    statsObserver.observe(statsSection);
}

// ============ ANIMATION AU CHARGEMENT DE LA PAGE ============
window.addEventListener('load', () => {
    const heroTitle = document.querySelector('h1');
    const heroParagraph = document.querySelector('section h1')?.nextElementSibling;
    const heroButtons = document.querySelector('.flex-wrap.gap-4');
    
    if (heroTitle) {
        heroTitle.style.opacity = '0';
        heroTitle.style.transform = 'translateY(30px)';
        heroTitle.style.transition = 'all 0.8s ease-out';
        setTimeout(() => {
            heroTitle.style.opacity = '1';
            heroTitle.style.transform = 'translateY(0)';
        }, 100);
    }
    
    if (heroParagraph) {
        heroParagraph.style.opacity = '0';
        heroParagraph.style.transform = 'translateY(30px)';
        heroParagraph.style.transition = 'all 0.8s ease-out';
        setTimeout(() => {
            heroParagraph.style.opacity = '1';
            heroParagraph.style.transform = 'translateY(0)';
        }, 300);
    }
    
    if (heroButtons) {
        heroButtons.style.opacity = '0';
        heroButtons.style.transform = 'translateY(30px)';
        heroButtons.style.transition = 'all 0.8s ease-out';
        setTimeout(() => {
            heroButtons.style.opacity = '1';
            heroButtons.style.transform = 'translateY(0)';
        }, 500);
    }
});

// ============ SMOOTH SCROLL POUR LES LIENS D'ANCRE ============
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        if (href !== '#') {
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        }
    });
});

// ============ ANIMATION DES CARTES AU SCROLL ============
const cardObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
});

document.querySelectorAll('.hover\\:-translate-y-2').forEach(card => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(30px)';
    card.style.transition = 'all 0.6s ease-out';
    cardObserver.observe(card);
});

// ============ PULSE EFFECT SUR LE BOUTON CTA ============
const ctaButton = document.querySelector('#cta a');
if (ctaButton) {
    setInterval(() => {
        ctaButton.style.animation = 'pulse 2s ease-in-out';
        setTimeout(() => {
            ctaButton.style.animation = '';
        }, 2000);
    }, 6000);
}