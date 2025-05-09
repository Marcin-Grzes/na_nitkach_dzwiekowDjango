from django.contrib.auth.models import User
from events.models import Rezerwations


def convert_guest_to_user(guest, username, password):
    """Konwertuje gościa na zarejestrowanego użytkownika """

    if guest.user is not None:
        return guest.user

    # Tworzenie nowego użytkownika
    user = User.objects.create_user(
        username=username,
        password=password,
        email=guest.email,
        first_name=guest.first_name,
        last_name=guest.last_name,
        )

    # Uzupełnienie profilu

    user.profile.phone_number = guest.phone_number
    user.profile.save()

    # Powiązanie gościa z użytkownikiem
    guest.user = user
    guest.save()

    # Przeniesienie rezerwacji
    for reservation in Rezerwations.objects.filter(guest=guest):
        reservation.user = user
        reservation.guest = None
        reservation.save()

    return user
