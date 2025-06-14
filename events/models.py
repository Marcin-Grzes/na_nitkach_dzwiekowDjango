import uuid

from django.db.models import Sum
from django.conf import settings
from django.db.models import Max
from django.urls import reverse
from django.utils import timezone
from .services import cancel_reservation
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from djmoney.models.validators import MinMoneyValidator
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from tinymce.models import HTMLField
from djmoney.models.fields import MoneyField
from djmoney.models.managers import money_manager
from accounts.models import Customer
from accounts.models_base import BaseMetadataModel
# Create your models here.


class Reservations(BaseMetadataModel):

    class ReservationStatus(models.TextChoices):
        CONFIRMED = 'confirmed', _('Potwierdzona')
        WAITLIST = 'waitlist', _('Lista rezerwowa')
        CANCELLED = 'cancelled', _('Anulowana')

    status = models.CharField(
        _("Status rezerwacji"),
        max_length=20,
        choices=ReservationStatus.choices,
        default=ReservationStatus.CONFIRMED,
    )

    """Relacja z modelem Customer z aplikacji accounts"""
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="reservations",
        verbose_name=_("Klient"),
        null=True,  # Ważne! Dodaj to, aby migracja mogła się wykonać na istniejących danych - Tymczasowo
    )

    """Dodaj pole pozycji na liście rezerwowej (przydatne do określenia kolejności)"""

    waitlist_position = models.PositiveIntegerField(
        _("Pozycja na liście rezerwowej"),
        null=True,
        blank=True,
        help_text=_("Pozycja na liście rezerwowej (tylko dla rezerwacji w statusie 'Lista rezerwowa')")
    )

    # Dodajemy pole tokenu
    cancellation_token = models.UUIDField(
        _("Token anulowania"),
        default=uuid.uuid4,
        editable=False,
        unique=True,
        # null=True,
        # Domyślnie na produkcji powinno tylko unique=True,
    )

    def get_cancellation_url(self):
        """Generuje pełny URL do anulowania rezerwacji"""
        path = reverse('cancel_reservation', kwargs={'token': self.cancellation_token})
        return f"{settings.SITE_URL}{path}"

    def cancel(self):
        """
        Metoda anulująca rezerwację - deleguje wykonanie do usługi
        """
        return cancel_reservation(self)

    class PaymentType(models.TextChoices):
        CASH = 'cash', _('Gotówka na miejscu')
        BLIK = 'blik', _('Przedpłata BLIK - 509553366 (w tytule imię, nazwisko i DATA!)')

    # Podstawowe informacje

    participants_count = models.PositiveIntegerField(
        _("Liczba uczestników"),
        default=1,
        validators=[
            MinValueValidator(1, _("Liczba uczestników musi wynosić co najmniej 1")),
            MaxValueValidator(100, _("Maksymalna liczba uczestników to 100"))
        ],
        help_text=_("Podaj liczbę osób biorących udział w spotkaniu.")
    )
    # Tu był pole email, phone_number

    type_of_payments = models.CharField(_("Typ płatności"), max_length=10,
                                        choices=PaymentType.choices, default=PaymentType.CASH)
    event = models.ForeignKey(
        'Events',
        on_delete=models.CASCADE,
        verbose_name=_("Wydarzenie"),
        related_name='reservations',
        null=True,  # Dodaj to tymczasowo
        blank=True  # Dodaj to tymczasowo
    )

    # Tu były pola zgód

    # Metadane
    # created_at = models.DateTimeField(_("Data utworzenia"), auto_now_add=True)

    class Meta:
        verbose_name = _("Rezerwacja")
        verbose_name_plural = _("Rezerwacje")

    def __str__(self):
        if self.customer:
            return f"{self.customer.first_name} {self.customer.last_name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
        else:
            return f"Rezerwacja #{self.id} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class Venue(BaseMetadataModel):
    name = models.CharField(_("Nazwa miejsca"), max_length=100)
    address = models.CharField(_("Adres"), max_length=255)
    city = models.CharField(_("Miasto"), max_length=100)
    postal_code = models.CharField(_("Kod pocztowy"), max_length=10)
    additional_info = models.TextField(_("Dodatkowe informacje"), blank=True)

    # Nowe pole na kod iframe z mapą Google
    map_iframe = models.TextField(
        _("Kod mapy Google"),
        blank=True,
        help_text=_(
            "Wklej tutaj kod iframe z Google Maps dla tego miejsca. Kod powinien zaczynać się od <iframe> i kończyć "
            "</iframe>.")
    )

    class Meta:
        verbose_name = _("Miejsce")
        verbose_name_plural = _("Miejsca")

    def __str__(self):
        return f"{self.name}, {self.address}, {self.city}"


class EventType(BaseMetadataModel):
    name = models.CharField(_("Nazwa typu"), max_length=100)
    description = models.TextField(_("Opis"), blank=True)
    slug = models.SlugField(_("Identyfikator"), unique=True)
    is_active = models.BooleanField(_("Aktywny"), default=True)

    class Meta:
        verbose_name = _("Typ wydarzenia")
        verbose_name_plural = _("Typy wydarzeń")
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Automatyczne generowanie slug, jeśli nie podano
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class EventImage(BaseMetadataModel):
    event = models.ForeignKey(
        'Events',
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_("Wydarzenie")
    )
    image = models.ImageField(
        _("Zdjęcie"),
        upload_to='event_images/'
    )
    caption = models.CharField(_("Podpis"), max_length=200, blank=True)
    order = models.PositiveIntegerField(_("Kolejność"), default=0)

    class Meta:
        verbose_name = _("Zdjęcie wydarzenia")
        verbose_name_plural = _("Zdjęcia wydarzeń")
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.event.title} - Zdjęcie {self.id}"


# Definicja niestandardowego menedżera
class EventManager(models.Manager):
    """
    Niestandardowy menedżer modelu Events z bezpiecznymi metodami
    aktualizacji statusów wydarzeń.
    """

    def get_queryset(self):
        """
        Podstawowa metoda get_queryset, która tylko zwraca dane
        bez wykonywania żadnych modyfikacji.

        Ta metoda jest jak bibliotekarz, który tylko wskazuje półkę z książkami,
        ale nie reorganizuje całej biblioteki za każdym razem.
        """
        return super().get_queryset()

    def update_past_events(self):
        """
               Dedykowana metoda do aktualizowania statusów minionych wydarzeń.
               Ta metoda powinna być wywoływana świadomie, gdy chcemy
               zsynchronizować statusy z rzeczywistością.

               Zwraca liczbę zaktualizowanych wydarzeń dla celów diagnostycznych.
               """
        # Znajdź wydarzenia, które już się rozpoczęły a są nadal aktywne
        past_events = self.get_queryset().filter(
            is_active=True,
            start_datetime__lt=timezone.now()
        )

        # Wykonaj aktualizację i zwróć liczbę zmodyfikowanych rekordów
        updated_count = past_events.update(is_active=False)

        return updated_count

    def active(self):
        """
        Pomocnicza metoda zwracająca tylko aktywne wydarzenia.
        """
        return self.get_queryset().filter(is_active=True)

    def upcoming(self):
        """
        Pomocnicza metoda zwracająca tylko przyszłe aktywne wydarzenia.
        """
        return self.active().filter(start_datetime__gte=timezone.now())

    def active_and_current(self):
        """
        Nowa metoda, która zwraca aktywne wydarzenia z automatyczną
        aktualizacją statusów. To jest bezpieczne miejsce na wywołanie
        aktualizacji, ponieważ nazwa metody jasno wskazuje, że wykona
        ona operację modyfikującą.
        """
        # Najpierw aktualizuj statusy
        updated_count = self.update_past_events()

        # Następnie zwróć aktywne wydarzenia
        return self.active()


class Events(BaseMetadataModel):
    title = models.CharField(_("Tytuł wydarzenia"), max_length=200)

    type_of_events = models.ForeignKey(
        EventType,
        on_delete=models.PROTECT,
        verbose_name=_("Typ wydarzenia"),
        related_name='events'
    )

    start_datetime = models.DateTimeField(_("Data i czas rozpoczęcia"))
    end_datetime = models.DateTimeField(_("Data i czas zakończenia"))

    venue = models.ForeignKey(
        'Venue',
        on_delete=models.PROTECT,
        verbose_name=_("Miejsce"),
        related_name='events'
    )
    price = MoneyField(_("Cena od osoby"),
                       max_digits=10,
                       decimal_places=2,
                       validators=[MinMoneyValidator(0)],
                       default_currency='PLN',
                       help_text=_("Cena za udział w wydarzeniu"),
                       null=True,
                       blank=True,)
    max_participants = models.PositiveIntegerField(
        _("Maksymalna liczba uczestników"),
        default=20,
        validators=[MinValueValidator(1)]
    )

    reserve_list = models.PositiveIntegerField(
        _("Lista rezerwowa"),
        default=0,  # defeault jest tymczasowo
    )

    # description = models.TextField(_("Opis wydarzenia"), blank=True)
    description = HTMLField(_("Opis wydarzenia"), blank=True)

    # Główne zdjęcie wydarzenia (opcjonalne)
    main_image = models.ImageField(
        _("Główne zdjęcie wydarzenia"),
        upload_to='event_main_images/',
        blank=True,
        null=True,
        help_text=_(
            "Główne zdjęcie przedstawiające wydarzenie. Dodatkowe zdjęcia można dodać po utworzeniu wydarzenia.")
    )

    objects = money_manager(EventManager())

    # Określenie momentu końca przyjmowania rezerwacji
    reservation_end_time = models.DateTimeField(
        _("Koniec przyjmowania rezerwacji"),
        null=True,
        blank=True,
        help_text=_("Po tej godzinie rezerwacja online nie będzie możliwa.")
    )

    # Metadane
    # created_at = models.DateTimeField(_("Data utworzenia"), auto_now_add=True)
    # updated_at = models.DateTimeField(_("Data aktualizacji"), auto_now=True)
    is_active = models.BooleanField(_("Aktywne"), default=True)

    class Meta:
        verbose_name = _("Wydarzenie")
        verbose_name_plural = _("Wydarzenia")
        ordering = ['-start_datetime']

    def __str__(self):
        return self.title

    def clean(self):
        # Walidacja dat - sprawdzanie czy data zakończenia jest po dacie rozpoczęcia
        if self.start_datetime and self.end_datetime:
            if self.end_datetime <= self.start_datetime:
                raise ValidationError({
                    'end_datetime': _("Data zakończenia musi być późniejsza niż data rozpoczęcia.")
                })

            # Opcjonalnie: sprawdzanie czy data rozpoczęcia nie jest w przeszłości
            # przy tworzeniu nowego wydarzenia
            if not self.id and self.start_datetime < timezone.now():
                raise ValidationError({
                    'start_datetime': _("Data rozpoczęcia nie może być w przeszłości.")
                })

    def is_reservation_available(self):
        """Sprawdza czy można jeszcze dokonać rezerwacji online."""
        if not self.reservation_end_time:
            return True
        return timezone.now() < self.reservation_end_time

    def save(self, *args, **kwargs):
        self.clean()  # Wywołanie walidacji przed zapisem
        super().save(*args, **kwargs)

    def get_confirmed_reservations_count(self):
        """Zwraca liczbę uczestników z potwierdzonych rezerwacji"""
        reservations = self.reservations.filter(status=Reservations.ReservationStatus.CONFIRMED)
        return sum(r.participants_count for r in reservations)

    def get_available_seats(self):
        """Zwraca liczbę dostępnych miejsc"""
        return max(0, self.max_participants - self.get_confirmed_reservations_count())

    def is_fully_booked(self):
        """Sprawdza czy wydarzenie jest w pełni zarezerwowane"""
        return self.get_available_seats() == 0

    def get_waitlist_count(self):
        """Zwraca liczbę osób na liście rezerwowej"""
        return self.reservations.filter(status=Reservations.ReservationStatus.WAITLIST).count()

    def get_waitlist_participants_count(self):
        """ Zwraca łączną liczbę uczestników na liście rezerwowej """
        result = self.reservations.filter(
            status=Reservations.ReservationStatus.WAITLIST
        ).aggregate(
            total=Sum('participants_count')
        )['total']
        return result or 0

    def get_next_waitlist_position(self):
        """Zwraca następną pozycję na liście rezerwowej"""
        max_position = self.reservations.filter(
            status=Reservations.ReservationStatus.WAITLIST
        ).aggregate(Max('waitlist_position'))['waitlist_position__max'] or 0
        return max_position + 1
