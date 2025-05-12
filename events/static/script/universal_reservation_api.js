// Globalne zmienne
let eventsData = {};

// Funkcja pobierająca dane wydarzeń z API
async function fetchEventsData() {
    try {
        console.log("Fetching events data from API...");
        const response = await fetch('/api/events-data/');
        if (!response.ok) {
            throw new Error('Network response was not ok: ' + response.status);
        }

        const data = await response.json();
        console.log("API response received:", data);

        // Zapisz dane do zmiennej globalnej
        eventsData = data;

        // Wypełnij select z opcjami wydarzeń
        populateEventSelector();

        // Zaktualizuj informacje na podstawie pierwszego wydarzenia
        updateEventInfo();

        console.log("Events data loaded successfully");
    } catch (error) {
        console.error('Error fetching events data:', error);
        document.getElementById('event-info').innerHTML = `
            <p class="reservation-form__text reservation-form__text--warning">
                <strong>Błąd:</strong> Nie udało się pobrać danych o wydarzeniach. 
                Spróbuj odświeżyć stronę lub skontaktuj się z administratorem.
            </p>
        `;
    }
}

// Funkcja wypełniająca selector z opcjami wydarzeń
function populateEventSelector() {
    const eventSelector = document.getElementById('event-selector');

    // Wyczyść istniejące opcje
    eventSelector.innerHTML = '';

    // Dodaj domyślną opcję
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = 'Wybierz wydarzenie';
    eventSelector.appendChild(defaultOption);

    // Dodaj opcje dla każdego wydarzenia
    for (const [eventId, event] of Object.entries(eventsData)) {
        const option = document.createElement('option');
        option.value = eventId;

        // Format daty dla wyświetlenia w selektorze
        const startDate = new Date(event.start_datetime);
        const formattedDate = startDate.toLocaleDateString('pl-PL', {
            day: 'numeric',
            month: 'long',
            year: 'numeric'
        });

        option.textContent = `${event.title} - ${formattedDate}`;
        eventSelector.appendChild(option);
    }

    console.log(`Populated selector with ${Object.keys(eventsData).length} events`);
}

// Funkcja aktualizująca informacje o wydarzeniu
function updateEventInfo() {
    const eventSelector = document.getElementById('event-selector');
    const eventInfo = document.getElementById('event-info');
    const submitButton = document.getElementById('submit-button');

    console.log("Updating event info for ID:", eventSelector.value);

    const selectedEventId = eventSelector.value;

    if (selectedEventId && eventsData[selectedEventId]) {
        const event = eventsData[selectedEventId];
        console.log("Selected event data:", event);

        // Format daty
        const startDate = new Date(event.start_datetime);

        // Przygotuj HTML z informacjami
        let infoHTML = `
            <p><span>Wydarzenie: </span>${event.title}</p>
            <p><span>Data: </span>${startDate.toLocaleDateString('pl-PL', { 
                day: 'numeric', 
                month: 'long', 
                year: 'numeric'
            })} ${startDate.toLocaleTimeString('pl-PL', {
                hour: '2-digit',
                minute: '2-digit'
            })}</p>
            <p><span>Miejsce: </span>${event.venue_name}, ${event.venue_address}, ${event.venue_city}</p>
            <p><span>Dostępne miejsca: </span>${event.available_seats}</p>
        `;

        // Dodaj cenę, jeśli istnieje
        if (event.price && event.price !== "Brak informacji") {
            infoHTML += `<p><span>Cena: </span>${event.price}</p>`;
        }

        // Dodaj ostrzeżenia
        if (event.is_fully_booked) {
            infoHTML += `
                <p class="reservation-form__text reservation-form__text--warning">
                    <strong>Uwaga:</strong> Wszystkie miejsca są już zajęte, ale możesz dołączyć do listy rezerwowej.
                </p>
            `;
        }

        if (!event.reservation_available) {
            infoHTML += `
                <p class="reservation-form__text reservation-form__text--warning">
                    <strong>Uwaga:</strong> Rezerwacja online na to wydarzenie jest już niedostępna. 
                    Skontaktuj się telefonicznie pod numerem 509 55 33 66.
                </p>
            `;
            submitButton.disabled = true;
        } else {
            submitButton.disabled = false;
        }

        // Zaktualizuj informacje
        eventInfo.innerHTML = infoHTML;
        eventInfo.classList.add('visible');

    } else {
        // Brak wybranego wydarzenia
        eventInfo.innerHTML = '<p><strong>Wybierz wydarzenie z listy, aby zobaczyć szczegóły</strong></p>';
        submitButton.disabled = true;
    }
}

// Inicjalizacja przy załadowaniu strony
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM loaded, initializing...");

    // Pobierz elementy DOM
    const eventSelector = document.getElementById('event-selector');

    if (eventSelector) {
        // Dodaj nasłuchiwanie zmiany wyboru wydarzenia
        eventSelector.addEventListener('change', updateEventInfo);

        // Pobierz dane z API
        fetchEventsData();
    } else {
        console.error("Event selector not found in DOM!");
    }
});