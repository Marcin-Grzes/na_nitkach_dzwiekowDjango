from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.utils.translation import gettext_lazy as _
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
        help_text=_("Podaj liczbę osób biorących udział w spotkaniu.")
    )
    email = models.EmailField(_("Adres email"))
    phone_number = PhoneNumberField(region='PL', verbose_name=_("Numer telefonu"))
    type_of_payments = models.CharField(_("Typ płatności"), max_length=10,
                                        choices=PaymentType.choices, default=PaymentType.CASH)

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
