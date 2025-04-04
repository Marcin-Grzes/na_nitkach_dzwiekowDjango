from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


# Zmieniona funkcja - nie używa self
def cancel_reservation(reservation):
    """Anuluje rezerwację i przesuwa osobę z listy rezerwowej jeśli istnieje"""
    from .models import Rezerwations  # Import wewnątrz funkcji by uniknąć cyklicznych importów

    if reservation.status == Rezerwations.ReservationStatus.CONFIRMED:
        # Zmiana statusu na anulowany
        reservation.status = Rezerwations.ReservationStatus.CANCELLED
        reservation.save()

        # Sprawdź czy są osoby na liście rezerwowej
        event = reservation.event
        waitlist_reservation = event.reservations.filter(
            status=Rezerwations.ReservationStatus.WAITLIST
        ).order_by('waitlist_position').first()

        if waitlist_reservation:
            # Przesuń osobę z listy rezerwowej na potwierdzoną
            waitlist_reservation.status = Rezerwations.ReservationStatus.CONFIRMED
            waitlist_reservation.waitlist_position = None
            waitlist_reservation.save()

            # Wyślij powiadomienie o potwierdzeniu rezerwacji
            send_waitlist_promotion_email(waitlist_reservation)

        return True
    return False


# Nowa funkcja do wysyłania powiadomień o przesunięciu z listy rezerwowej
def send_waitlist_promotion_email(reservation):
    subject = f'Potwierdzenie rezerwacji - {reservation.event.title}'

    context = {
        'reservation': reservation,
        'event': reservation.event,
        'first_name': reservation.first_name,
        'last_name': reservation.last_name,
    }

    html_message = render_to_string('emails/waitlist_promotion_notification.html', context)
    plain_message = strip_tags(html_message)

    send_mail(
        subject,
        plain_message,
        None,  # używa DEFAULT_FROM_EMAIL z ustawień
        [reservation.email],
        html_message=html_message,
    )
