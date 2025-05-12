// Globalna zmienna na dane wydarzeń - będzie ustawiona przez inline script

let eventsData = {};

// Funkcja aktualizująca informacje o wydarzeniu

const updateEventInfo = function () {
    const eventSelector = document.getElementById('event-selector');
    const eventInfo = document.getElementById('event-info');
    const submitButton = document.getElementById('submit-button');
    console.log("DOM elements:", {
        eventSelector,
        eventInfo,
        submitButton
    });

    const selectedEventId = eventSelector.value;
    console.log("Selected event ID:", selectedEventId);
    console.log("Available events:", Object.keys(eventsData));
    console.log("Event data for selected ID:", eventsData[selectedEventId]);

    if (selectedEventId && eventsData[selectedEventId]) {
        const event = eventsData[selectedEventId];
        const startDate = new Date(event.start_datetime);

        let infoHTML = `
    <p><span>Wydarzenie: </span>${event.title}</p>
    <p><span>Data: </span>${startDate.toLocaleDateString('pl-PL', { 
        day: 'numeric', 
        month: 'long', 
        year: 'numeric', 
        hour: '2-digit', 
        minute: '2-digit' 
    })}</p>
    <p><span>Miejsce: </span>${event.venue_name}, ${event.venue_address}, ${event.venue_city}</p>
    <p><span>Dostępne miejsca: </span>${event.available_seats}</p>
`;

        if (event.price && event.price !== 'Brak informacji') {
            infoHTML += `<p>${event.price}</p>`;
        }

        // Wyświetl ostrzeżenie, jeśli wydarzenie jest w pełni zarezerwowane
        if (event.is_fully_booked) {
            infoHTML += '<p class="reservation-form__text reservation-form__text--warning">' +
                '<strong>Uwaga:</strong> Wszystkie miejsca są już zajęte, ale możesz dołączyć do listy rezerwowej</p>';
        }
        // Wyświetl informację, jeśli rezerwacja nie jest już dostępna
        if (!event.reservation_available) {
            infoHTML += '<p class="reservation-form__text reservation-form__text--warning">' +
                '<strong>Uwaga:</strong> Rezerwacja online na to wydarzenie jest już niedostepna. Skontaktuj się telefonicznie.' +
                '</p>';
            submitButton.disabled = true;
        } else {
            submitButton.disabled = false;
        }

        eventInfo.innerHTML = infoHTML;
        eventInfo.classList.add('visible');
    } else {
        eventInfo.innerHTML = '<p><strong>Wybierz wydarenie z listy, aby zobaczyć szczegóły</strong></p>';
        submitButton.disabled = true;
    }
}

// Inicjalizacja przy załadowaniu strony

document.addEventListener('DOMContentLoaded', function (){
    const eventSelector = document.getElementById('event-selector');
    if (eventSelector) {
        console.log("Found event selector with value:", eventSelector.value);
        // Dodaj nasłuchiwanie na zmiany w selektorze wydarzeń
        eventSelector.addEventListener('change', updateEventInfo);
        // Początkowa aktualizacja
        updateEventInfo();
    } else {
        console.error("Event selector not found in DOM!");
    }
});