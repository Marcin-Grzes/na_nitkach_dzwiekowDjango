document.addEventListener('DOMContentLoaded', function () {
    // Inicjalizacja kalendarza
    let calendarEl = document.getElementById('calendar');
    let calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        locale: 'pl',
        firstDay: 1,  // Ustawia poniedziałek jako pierwszy dzień tygodnia
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
        /*eventDidMount: function (info) {
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
<!--                    -->
                        <p>
                ${!isFullyBooked
                    ? `<a href="/events/${info.event.id}/reservation/" class="btn btn-primary btn-sm">Zarezerwuj miejsce</a>`
                    : `<button class="btn btn-secondary btn-sm" disabled>Brak miejsc</button>`
                }
            </p>
        </div>
    \`,
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
        },*/
        windowResize: function (view) {
            if (window.innerWidth < 768) {
                calendar.changeView('listMonth');
            } else {
                calendar.changeView('dayGridMonth');
            }
        },

        // Sprawdź szerokość ekranu podczas inicjalizacji
        viewDidMount: function () {
            if (window.innerWidth < 768) {
                calendar.changeView('listMonth');
            }
        }
    });
    calendar.render();

    // Obsługa filtrowania po typie wydarzenia
    /*document.getElementById('event-type-filter').addEventListener('change', function () {
        const selectedType = this.value;

        // Odśwież kalendarz z filtrem typu
        calendar.getEventSources()[0].remove();
        calendar.addEventSource({
            url: '/api/calendar-events/' + (selectedType ? '?type=' + selectedType : '')
        });
    });*/

    // Obsługa przełącznika pokazywania w pełni zarezerwowanych wydarzeń
    /*document.getElementById('show-fully-booked').addEventListener('change', function () {
        const fullyBookedEvents = document.querySelectorAll('.fully-booked');

        fullyBookedEvents.forEach(function (eventEl) {
            if (this.checked) {
                eventEl.style.display = '';
            } else {
                eventEl.style.display = 'none';
            }
        }, this);
    });*/

    // Pomocnicza funkcja formatowania daty
    function formatDate(date) {
        const options = {year: 'numeric', month: 'long', day: 'numeric'};
        return new Date(date).toLocaleDateString('pl-PL', options);
    }

    // Pomocnicza funkcja formatowania czasu
    function formatTime(date) {
        const options = {hour: '2-digit', minute: '2-digit'};
        return new Date(date).toLocaleTimeString('pl-PL', options);
    }
});