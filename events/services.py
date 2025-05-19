from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


# Zmieniona funkcja - nie używa self
def cancel_reservation(reservation):
    """Anuluje rezerwację i przesuwa osobę z listy rezerwowej jeśli istnieje"""
    from .models import Reservations  # Import wewnątrz funkcji by uniknąć cyklicznych importów

    if reservation.status == Reservations.ReservationStatus.CONFIRMED:
        # Zmiana statusu na anulowany
        reservation.status = Reservations.ReservationStatus.CANCELLED
        reservation.save()

        # Sprawdź czy są osoby na liście rezerwowej
        event = reservation.event
        waitlist_reservation = event.reservations.filter(
            status=Reservations.ReservationStatus.WAITLIST
        ).order_by('waitlist_position').first()

        if waitlist_reservation:
            # Przesuń osobę z listy rezerwowej na potwierdzoną
            waitlist_reservation.status = Reservations.ReservationStatus.CONFIRMED
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
        'first_name': reservation.customer.first_name,
        'last_name': reservation.customer.last_name,
        'participants_count': reservation.participants_count,
        'email': reservation.customer.email,
        'phone_number': str(reservation.customer.phone_number),
        'payment_method': reservation.get_type_of_payments_display(),
    }

    html_message = render_to_string('mail/mail_event_reservation_confirmation.html', context)
    plain_message = strip_tags(html_message)

    send_mail(
        subject,
        plain_message,
        None,  # używa DEFAULT_FROM_EMAIL z ustawień
        [reservation.customer.email],
        html_message=html_message,
    )
