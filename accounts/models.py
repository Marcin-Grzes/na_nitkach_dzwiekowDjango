from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.utils.translation import gettext_lazy as _
from .models_base import BaseMetadataModel

# Create your models here.


class Customer(BaseMetadataModel):
    """
    Model użytkownika dokonującego rezerwacji bez powiązania z systemem authenticity Django.
    Bez logowania i rejestracji
    """
    first_name = models.CharField(_("Imię"), max_length=50)
    last_name = models.CharField(_("Nazwisko"), max_length=50)
    email = models.EmailField(_("Adres email"))
    phone_number = PhoneNumberField(region='PL', verbose_name=_("Numer telefonu"))

    # Pola zgód
    regulations_consent = models.BooleanField(
        _("Akceptacja regulaminu i polityki prywatności"),
        default=False,
        help_text=_("Zapoznałem się z regulaminem oraz polityką prywatności")
    )

    newsletter_consent = models.BooleanField(
        _("Zapis na newsletter"),
        default=False,
        help_text=_("Chcę zapisać się na newsletter, by otrzymywać informacje o przyszłych wydarzeniach i ofertach "
                    "specjalnych.")
    )

    class Meta:
        verbose_name = _("Klient")
        verbose_name_plural = _("Klienci")
        """Dodajemy unikalność dla kombinacji email i numer telefonu"""
        unique_together = ["email"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} {self.email}"

    def get_full_name(self):
        """Zwraca pelne imię i nazwisko"""
        return f"{self.first_name} {self.last_name}"
