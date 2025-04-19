document.addEventListener('DOMContentLoaded', function() {
    // Funkcja do inicjalizacji lazy-loadingu obrazów
    function initLazyLoading() {
        // Wybierz wszystkie obrazy z klasą lazy-image
        const lazyImages = document.querySelectorAll('.lazy-image');

        // Jeśli Intersection Observer API jest dostępne
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver(function(entries, observer) {
                entries.forEach(function(entry) {
                    // Jeśli obraz jest widoczny
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        // Załaduj właściwy obraz jeśli ma data-src
                        if (img.dataset.src) {
                            img.src = img.dataset.src;

                            // Gdy obraz się załaduje, dodaj klasę 'loaded'
                            img.onload = function() {
                                img.classList.add('loaded');

                                // Szukamy kontenera nadrzędnego dla obrazka
                                const container = img.closest('.concerts__image-placeholder') ||
                                    img.closest('.image-placeholder') ||
                                    img.parentNode;

                                if (container) {
                                    container.classList.add('loaded');
                                }
                            };
                        }

                        // Przestań obserwować ten obraz
                        observer.unobserve(img);
                    }
                });
            }, {
                // Opcje Intersection Observer
                rootMargin: '50px 0px', // Ładuj obrazy 50px przed wejściem w obszar widoczny
                threshold: 0.01 // Ładuj gdy 1% obrazu jest widoczny
            });

            // Obserwuj każdy obraz z klasą lazy-image
            lazyImages.forEach(function(image) {
                imageObserver.observe(image);
            });
        } else {
            // Fallback dla przeglądarek, które nie obsługują Intersection Observer
            lazyLoadImagesFallback(lazyImages);
        }
    }

    // Funkcja zastępcza dla starszych przeglądarek
    function lazyLoadImagesFallback(lazyImages) {
        // Prosta implementacja oparta na zdarzeniach scroll
        function loadImagesInView() {
            lazyImages.forEach(function(img) {
                if (isElementInViewport(img) && img.dataset.src) {
                    img.src = img.dataset.src;
                    img.onload = function() {
                        img.classList.add('loaded');
                    };
                    // Usuń z listy ładowanych leniwie
                    img.removeAttribute('data-src');
                }
            });

            // Filtruj obrazy, które zostały już załadowane
            lazyImages = Array.from(lazyImages).filter(function(img) {
                return img.hasAttribute('data-src');
            });

            // Jeśli wszystkie obrazy zostały załadowane, usuń nasłuchiwanie zdarzeń
            if (lazyImages.length === 0) {
                window.removeEventListener('scroll', lazyScrollHandler);
                window.removeEventListener('resize', lazyScrollHandler);
                window.removeEventListener('orientationchange', lazyScrollHandler);
            }
        }

        // Funkcja pomocnicza do sprawdzania, czy element jest widoczny
        function isElementInViewport(el) {
            const rect = el.getBoundingClientRect();
            return (
                rect.top >= 0 &&
                rect.left >= 0 &&
                rect.top <= (window.innerHeight || document.documentElement.clientHeight) + 100
            );
        }

        // Opóźnienie obsługi przewijania dla wydajności
        let lazyScrollHandler = debounce(loadImagesInView, 200);

        // Nasłuchiwanie zdarzeń
        window.addEventListener('scroll', lazyScrollHandler);
        window.addEventListener('resize', lazyScrollHandler);
        window.addEventListener('orientationchange', lazyScrollHandler);

        // Uruchom raz na początku
        loadImagesInView();
    }

    // Funkcja pomocnicza debounce, aby ograniczyć ilość wywoływań funkcji
    function debounce(func, wait) {
        let timeout;
        return function() {
            const context = this;
            const args = arguments;
            clearTimeout(timeout);
            timeout = setTimeout(function() {
                func.apply(context, args);
            }, wait);
        };
    }

    // Inicjalizacja lazy-loadingu - upewnij się, że to się wykonuje
    initLazyLoading();
});
