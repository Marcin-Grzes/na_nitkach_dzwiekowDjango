document.addEventListener('DOMContentLoaded', function() {
    const cookieConsent = {
        init: function() {
            // Sprawdź, czy użytkownik już wyraził zgodę
            if (!this.hasConsent()) {
                this.showBanner();
            }
            this.bindEvents();
        },

        hasConsent: function() {
            return localStorage.getItem('cookieConsent') === 'accepted';
        },

        setConsent: function(value) {
            localStorage.setItem('cookieConsent', value);
            localStorage.setItem('cookieConsentDate', new Date().toISOString());
        },

        showBanner: function() {
            const banner = document.createElement('div');
            banner.className = 'cookie-banner';
            banner.innerHTML = `
                <div class="cookie-banner__container">
                    <div class="cookie-banner__content">
                        <p>Ta strona używa plików cookie, aby zapewnić najlepsze doświadczenie użytkowania. 
                        Korzystając z tej strony, zgadzasz się na używanie plików cookie zgodnie z naszą 
                        <a href="/polityka-prywatnosci/" target="_blank">polityką prywatności</a>.</p>
                    </div>
                    <div class="cookie-banner__buttons">
                        <button class="cookie-banner__button cookie-banner__button--accept">Akceptuję wszystkie</button>
                        <button class="cookie-banner__button cookie-banner__button--necessary">Tylko niezbędne</button>
                        <button class="cookie-banner__button cookie-banner__button--settings">Ustawienia</button>
                    </div>
                </div>
            `;
            document.body.appendChild(banner);

            // Pokazanie bannera z animacją
            setTimeout(() => {
                banner.classList.add('cookie-banner--visible');
            }, 100);
        },

        hideBanner: function() {
            const banner = document.querySelector('.cookie-banner');
            if (banner) {
                banner.classList.remove('cookie-banner--visible');
                setTimeout(() => {
                    banner.remove();
                }, 300);
            }
        },

        showSettings: function() {
            const settings = document.createElement('div');
            settings.className = 'cookie-settings';
            settings.innerHTML = `
                <div class="cookie-settings__overlay">
                    <div class="cookie-settings__container">
                        <div class="cookie-settings__header">
                            <h3>Ustawienia plików cookie</h3>
                            <button class="cookie-settings__close">&times;</button>
                        </div>
                        <div class="cookie-settings__content">
                            <div class="cookie-settings__option">
                                <label>
                                    <input type="checkbox" name="necessary" checked disabled>
                                    <span class="cookie-settings__option-title">Niezbędne pliki cookie</span>
                                </label>
                                <p>Te pliki są niezbędne do działania strony i nie mogą być wyłączone. Obejmują pliki cookie sesyjne, które pozwalają na korzystanie z formularza rezerwacji.</p>
                            </div>
                            <div class="cookie-settings__option">
                                <label>
                                    <input type="checkbox" name="analytics" id="analytics-checkbox">
                                    <span class="cookie-settings__option-title">Pliki cookie analityczne</span>
                                </label>
                                <p>Pomagają nam zrozumieć, w jaki sposób użytkownicy korzystają z witryny, co pozwala na jej ulepszanie.</p>
                            </div>
                            <div class="cookie-settings__option">
                                <label>
                                    <input type="checkbox" name="marketing" id="marketing-checkbox">
                                    <span class="cookie-settings__option-title">Pliki cookie marketingowe</span>
                                </label>
                                <p>Służą do personalizacji reklam i śledzenia skuteczności kampanii marketingowych.</p>
                            </div>
                        </div>
                        <div class="cookie-settings__footer">
                            <button class="cookie-settings__button cookie-settings__button--save">Zapisz preferencje</button>
                            <a href="/polityka-prywatnosci/" target="_blank" class="cookie-settings__link">Polityka prywatności</a>
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(settings);

            // Pokazanie ustawień z animacją
            setTimeout(() => {
                settings.classList.add('cookie-settings--visible');
            }, 100);

            this.bindSettingsEvents(settings);
        },

        bindSettingsEvents: function(settings) {
            // Zamknięcie ustawień
            settings.querySelector('.cookie-settings__close').addEventListener('click', () => {
                this.hideSettings(settings);
            });

            settings.querySelector('.cookie-settings__overlay').addEventListener('click', (e) => {
                if (e.target === settings.querySelector('.cookie-settings__overlay')) {
                    this.hideSettings(settings);
                }
            });

            // Zapisanie preferencji
            settings.querySelector('.cookie-settings__button--save').addEventListener('click', () => {
                const analytics = settings.querySelector('#analytics-checkbox').checked;
                const marketing = settings.querySelector('#marketing-checkbox').checked;

                // Zapisz preferencje
                this.setConsent('accepted');
                localStorage.setItem('cookieAnalytics', analytics ? 'accepted' : 'rejected');
                localStorage.setItem('cookieMarketing', marketing ? 'accepted' : 'rejected');

                this.hideSettings(settings);
                this.hideBanner();

                // Opcjonalnie: przeładuj stronę aby zastosować nowe ustawienia
                // window.location.reload();
            });
        },

        hideSettings: function(settings) {
            settings.classList.remove('cookie-settings--visible');
            setTimeout(() => {
                settings.remove();
            }, 300);
        },

        bindEvents: function() {
            document.addEventListener('click', (e) => {
                if (e.target.closest('.cookie-banner__button--accept')) {
                    // Akceptuj wszystkie pliki cookie
                    this.setConsent('accepted');
                    localStorage.setItem('cookieAnalytics', 'accepted');
                    localStorage.setItem('cookieMarketing', 'accepted');
                    this.hideBanner();
                }

                if (e.target.closest('.cookie-banner__button--necessary')) {
                    // Akceptuj tylko niezbędne pliki cookie
                    this.setConsent('accepted');
                    localStorage.setItem('cookieAnalytics', 'rejected');
                    localStorage.setItem('cookieMarketing', 'rejected');
                    this.hideBanner();
                }

                if (e.target.closest('.cookie-banner__button--settings')) {
                    this.showSettings();
                }
            });
        },

        // Publiczne metody do sprawdzania zgód
        hasAnalyticsConsent: function() {
            return localStorage.getItem('cookieAnalytics') === 'accepted';
        },

        hasMarketingConsent: function() {
            return localStorage.getItem('cookieMarketing') === 'accepted';
        }
    };

    // Inicjalizacja
    cookieConsent.init();

    // Udostępnienie globalnie dla innych skryptów
    window.cookieConsent = cookieConsent;
});