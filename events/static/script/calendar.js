document.addEventListener('DOMContentLoaded', function() {
    // Inicjalizacja kalendarza
    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        locale: 'pl',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,listMonth'
        },
        buttonText: {
            today: 'Dzisiaj',
            month: 'Miesiąc',
            week: 'Tydzień',
            list: 'Lista'
        },
        events: '/api/calendar-events/',
        eventTimeFormat: {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        },
        dayMaxEvents: true,
        eventDidMount: function(info) {
            // Dodaj tooltips do wydarzeń
            const props = info.event.extendedProps;
            const seats = props.available_seats;
            const isFullyBooked = props.is_fully_booked;

            // Dodaj klasę dla w pełni zarezerwowanych wydarzeń
            if (isFullyBooked) {
                info.el.classList.add('fully-booked');
            }

            // Utwórz tooltip
            tippy(info.el, {
                content: `
                    <div class="event-tooltip">
                        <h5>${info.event.title}</h5>
                        <p>
                            <strong>Kiedy:</strong> ${formatDate(info.event.start)} - ${formatTime(info.event.start)} do ${formatTime(info.event.end)}
                        </p>
                        <p><strong>Gdzie:</strong> ${props.venue}</p>
                        <p><strong>Typ:</strong> ${props.event_type}</p>
                        <p>
                            <strong>Status:</strong> 
                            ${isFullyBooked 
                                ? '<span class="text-danger">Brak miejsc</span>' 
                                : `<span class="text-success">Dostępne miejsca: ${seats}</span>`
                            }
                        </p>
                        <em>Kliknij, aby zobaczyć szczegóły</em>
                    </div>
                `,
                allowHTML: true,
                placement: 'top',
                arrow: true,
                theme: 'light'
            });
        }
    });
    calendar.render();

    // Obsługa filtrowania po typie wydarzenia
    document.getElementById('event-type-filter').addEventListener('change', function() {
        const selectedType = this.value;

        // Odśwież kalendarz z filtrem typu
        calendar.getEventSources()[0].remove();
        calendar.addEventSource({
            url: '/api/calendar-events/' + (selectedType ? '?type=' + selectedType : '')
        });
    });

    // Obsługa przełącznika pokazywania w pełni zarezerwowanych wydarzeń
    document.getElementById('show-fully-booked').addEventListener('change', function() {
        const fullyBookedEvents = document.querySelectorAll('.fully-booked');

        fullyBookedEvents.forEach(function(eventEl) {
            if (this.checked) {
                eventEl.style.display = '';
            } else {
                eventEl.style.display = 'none';
            }
        }, this);
    });

    // Pomocnicza funkcja formatowania daty
    function formatDate(date) {
        const options = { year: 'numeric', month: 'long', day: 'numeric' };
        return new Date(date).toLocaleDateString('pl-PL', options);
    }

    // Pomocnicza funkcja formatowania czasu
    function formatTime(date) {
        const options = { hour: '2-digit', minute: '2-digit' };
        return new Date(date).toLocaleTimeString('pl-PL', options);
    }
});