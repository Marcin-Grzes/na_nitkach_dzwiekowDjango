// Dodaj na początku pliku
console.log("Skrypt reservation-availability.js zaczyna się ładować");

/**
 * Moduł do sprawdzania dostępności rezerwacji wydarzenia
 * Monitoruje czas i dynamicznie aktualizuje UI gdy rezerwacja staje się niedostępna
 */
const ReservationAvailability = {
    /**
     * Inicjalizacja monitorowania dostępności rezerwacji
     * @param {string} elementId - ID kontenera z przyciskiem rezerwacji
     */
    init: function() {
        document.addEventListener('DOMContentLoaded', function() {
            // Pobierz elementy DOM i dane z data-atrybutów
            const buttonContainer = document.getElementById('reservation-button-container');

            // Sprawdź czy elementy istnieją
            if (!buttonContainer) return;

            // Pobierz czas końca rezerwacji z atrybutu data
            const endTimeISO = buttonContainer.getAttribute('data-reservation-end-time');
            if (!endTimeISO) return;

            const reservationEndTime = new Date(endTimeISO);

            // Funkcja sprawdzająca dostępność rezerwacji
            function checkAvailability() {
                const now = new Date();

                if (now >= reservationEndTime) {
                    // Czas rezerwacji minął - aktualizujemy UI
                    buttonContainer.innerHTML = `
                        <div class="event-detail__cta-notice">
                            Rezerwacja online jest już niedostępna, jeśli chcesz przyjść na koncert to zadzwoń.
                        </div>
                    `;
                }
            }

            // Sprawdzaj co 30 sekund
            checkAvailability();
            const intervalId = setInterval(checkAvailability, 1000);

            // Zatrzymaj interwał gdy strona jest ukryta
            document.addEventListener('visibilitychange', function() {
                if (document.hidden) {
                    clearInterval(intervalId);
                } else {
                    // Sprawdź natychmiast po powrocie do strony i ustaw nowy interwał
                    checkAvailability();
                    setInterval(checkAvailability, 90000);
                }
            });
        });
    },

    /**
     * Inicjalizacja monitorowania formularza rezerwacji
     * Sprawdza dostępność rezerwacji przez API
     * @param {string} apiEndpoint - URL endpointu API do sprawdzania dostępności
     */
    initFormMonitoring: function(apiEndpoint) {
        document.addEventListener('DOMContentLoaded', function() {
            const formContainer = document.getElementById('reservation-form-container');
            if (!formContainer) return;

            // Funkcja do sprawdzania dostępności rezerwacji przez API
            function checkReservationAvailability() {
                fetch(apiEndpoint)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Network response was not ok');
                        }
                        return response.json();
                    })
                    .then(data => {
                        console.log('Reservation availability status:', data);

                        if (!data.available) {
                            // Jeśli rezerwacja nie jest już dostępna, podmień formularz na komunikat
                            formContainer.innerHTML = `
                                <div class="reservation-form__information reservation-form__unavailable">
                                    <p class="reservation-form__text reservation-form__text--warning">
                                        ${data.message || "Rezerwacja online jest już niedostępna, jeśli chcesz przyjść na koncert to zadzwoń."}
                                    </p>
                                    <div class="reservation-form__form-buttons">
                                        <a href="${formContainer.getAttribute('data-event-detail-url')}" class="btn btn-secondary">Powrót</a>
                                    </div>
                                </div>
                            `;
                        }
                    })
                    .catch(error => {
                        console.error('Error checking reservation availability:', error);
                    });
            }

            // Sprawdź dostępność przy załadowaniu strony
            checkReservationAvailability();

            // Ustawiamy interwał do regularnego sprawdzania (co 30 sekund)
            const intervalId = setInterval(checkReservationAvailability, 30000);

            // Zatrzymaj interwał gdy strona jest ukryta
            document.addEventListener('visibilitychange', function() {
                if (document.hidden) {
                    clearInterval(intervalId);
                } else {
                    // Sprawdź natychmiast po powrocie do strony i ustaw nowy interwał
                    checkReservationAvailability();
                    setInterval(checkReservationAvailability, 30000);
                }
            });
        });
    }
};
// Automatycznie inicjalizuj gdy dokument jest gotowy
// Na końcu pliku reservation-availability.js
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM załadowany - pierwsza próba inicjalizacji");
    try {
        ReservationAvailability.init();
    } catch(e) {
        console.error("Błąd podczas inicjalizacji na DOMContentLoaded:", e);
    }
});

window.addEventListener('load', function() {
    console.log("Strona w pełni załadowana - druga próba inicjalizacji");
    try {
        ReservationAvailability.init();
    } catch(e) {
        console.error("Błąd podczas inicjalizacji na window.load:", e);
    }
});

// Na końcu pliku
console.log("Skrypt reservation-availability.js załadowany");