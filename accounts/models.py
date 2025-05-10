from django.contrib.auth.models import AbstractUser, User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from phonenumber_field.modelfields import PhoneNumberField
from django.utils.translation import gettext_lazy as _

# Create your models here.


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = PhoneNumberField(_('Numer telefonu'), region='PL', blank=True)

    # Pole określające, czy użytkownik był początkowo niezarejestrowany
    was_guest = models.BooleanField(_('Był gościem'), default=False)

    # Możemy dodać więcej pól w przyszłości

    class Meta:
        verbose_name = _('Profil użytkownika')
        verbose_name_plural = _('Profil użytkownika')

    def __str__(self):
        # Dostosowana metoda __str__ odwołująca się do powiązanego User
        if self.user.email:
            return f"Profil: {self.user.email}"
        else:
            return f"Profil: {self.user.username}"


# Sygnały do automatycznego tworzenia profilu
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
        if created:
            UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class GuestUser(models.Model):
    """
    Model przechowujący dane niezarejestrowanych użytkowników (gości),
    którzy dokonali rezerwacji. W przyszłości może zostać połączony z pełnym kontem użytkownika
    """

    first_name = models.CharField(_('Imię'), max_length=50)
    last_name = models.CharField(_('Nazwisko'), max_length=50)
    email = models.EmailField(_('Adres email'))
    phone_number = PhoneNumberField(_('Numer telefonu'), region='PL')
    created_at = models.DateTimeField(_('Data utworzenia'), auto_now_add=True)

    # Pola zgód przeniesione z modelu Rezerwations
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

    # Odniesienie do pełnego konta użytkownika (początkowo NULL)
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='guest_profile',
        verbose_name=_('Powiązane konto')
    )

    class Meta:
        verbose_name = _('Użytkownik-gość')
        verbose_name_plural = _('Użytkownicy-goście')
        constraints = [
            # Unikalność e-mail
            models.UniqueConstraint(fields=['email'], name='unique_guest'),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} {self.email}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    # def convert_to_registered_user(self, username, password):
    #     """Konwertuje gościa na pełnoprawnego użytkownika"""
    #     if self.user is None:
    #         return self.user
    #
    #     user = CustomUser.objects.create_user(
    #         username=username,
    #         email=self.email,
    #         password=password,
    #         first_name=self.first_name,
    #         last_name=self.last_name,
    #         phone_number=self.phone_number,
    #         was_guest=True
    #     )
    #
    #     self.user = user
    #     self.save()
    #     return user
