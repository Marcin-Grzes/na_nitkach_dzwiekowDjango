from django.utils import timezone

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from phonenumber_field.modelfields import PhoneNumberField
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from tinymce.models import HTMLField


# Create your models here.


class Rezerwations(models.Model):
    class PaymentType(models.TextChoices):
        CASH = 'cash', _('Gotówka na miejscu')
        BLIK = 'blik', _('BLIK')

    # Podstawowe informacje
    first_name = models.CharField(_("Imię"), max_length=50)
    last_name = models.CharField(_("Nazwisko"), max_length=50)
    participants_count = models.PositiveIntegerField(
        _("Liczba uczestników"),
        default=1,
        validators=[
            MinValueValidator(1, _("Liczba uczestników musi wynosić co najmniej 1")),
            MaxValueValidator(100, _("Maksymalna liczba uczestników to 100"))
        ],
        help_text=_("Podaj liczbę osób biorących udział w spotkaniu.")
    )
    email = models.EmailField(_("Adres email"))
    phone_number = PhoneNumberField(region='PL', verbose_name=_("Numer telefonu"))
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
    # Pola zgód
    data_processing_consent = models.BooleanField(
        _("Zgoda na przetwarzanie danych"),
        default=False,
        help_text=_("Wyrażam zgodę na przetwarzanie moich danych osobowych niezbędnych do realizacji spotkania.")
    )

    privacy_policy_consent = models.BooleanField(
        _("Zgoda na politykę prywatności"),
        default=False,
        help_text=_("Oświadczam, że zapoznałem się z polityką prywatności i akceptuję jej warunki.")
    )

    marketing_emails_consent = models.BooleanField(
        _("Zgoda marketingowa"),
        default=False,
        help_text=_("Wyrażam zgodę na otrzymywanie informacji o przyszłych wydarzeniach i ofertach specjalnych.")
    )

    reminder_emails_consent = models.BooleanField(
        _("Zgoda na przypomnienie o spotkaniu"),
        default=False,
        help_text=_("Wyrażam zgodę na otrzymywanie przypomnienia o zbliżającym się koncercie")
    )

    # Metadane
    created_at = models.DateTimeField(_("Data utworzenia"), auto_now_add=True)

    class Meta:
        verbose_name = _("Rezerwacja")
        verbose_name_plural = _("Rezerwacje")

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class Venue(models.Model):
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


class EventType(models.Model):
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


class EventImage(models.Model):
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


class Events(models.Model):
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

    max_participants = models.PositiveIntegerField(
        _("Maksymalna liczba uczestników"),
        default=20,
        validators=[MinValueValidator(1)]
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

    # Metadane
    created_at = models.DateTimeField(_("Data utworzenia"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Data aktualizacji"), auto_now=True)
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

    def save(self, *args, **kwargs):
        self.clean()  # Wywołanie walidacji przed zapisem
        super().save(*args, **kwargs)

    def get_available_seats(self):
        """Zwraca liczbę dostępnych miejsc"""
        reserved = self.reservations.count()
        return max(0, self.max_participants - reserved)

    def is_fully_booked(self):
        """Sprawdza czy wydarzenie jest w pełni zarezerwowane"""
        return self.get_available_seats() == 0
