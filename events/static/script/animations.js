document.addEventListener('DOMContentLoaded', function() {
    // Funkcja inicjalizująca animacje podczas przewijania
    function initScrollAnimations() {
        const elements = document.querySelectorAll('.fade-in-element');

        if ('IntersectionObserver' in window) {
            const elementObserver = new IntersectionObserver(function(entries, observer) {
                entries.forEach(function(entry) {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('visible');
                        // Opcjonalnie, przestań obserwować element po jego animacji
                        // observer.unobserve(entry.target);
                    }
                });
            }, {
                rootMargin: '0px',
                threshold: 0.1 // Animacja rozpocznie się, gdy 10% elementu jest widoczne
            });

            elements.forEach(function(element) {
                elementObserver.observe(element);
            });
        } else {
            // Fallback dla starszych przeglądarek - pokazuj wszystkie elementy
            elements.forEach(function(element) {
                element.classList.add('visible');
            });
        }
    }

    // Inicjalizacja animacji
    initScrollAnimations();
});