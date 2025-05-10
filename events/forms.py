from django import forms

from accounts.models import GuestUser
from .models import Rezerwations, Events, EventType, Venue



class EventForm(forms.ModelForm):
    class Meta:
        model = Events
        fields = [
            'title', 'type_of_events', 'start_datetime', 'end_datetime',
            'venue', 'price', 'max_participants', 'description', 'main_image', 'is_active'
        ]
        widgets = {
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 5}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_datetime = cleaned_data.get('start_datetime')
        end_datetime = cleaned_data.get('end_datetime')

        if start_datetime and end_datetime:
            if end_datetime <= start_datetime:
                self.add_error('end_datetime',
                               "Data zakończenia musi być późniejsza niż data rozpoczęcia.")

        return cleaned_data


class EventReservationForm(forms.ModelForm):
    """
    Formularz dla rezerwacji na konkretne wydarzenie.
    Pole 'event' jest ukryte i wypełniane automatycznie.
    """

    """Formularz rezerwacji obsługujący zarówno użytkowników zalogowanych jak i gości"""
    # Pola dla użytkowników niezalogowanych

    first_name = forms.CharField(label="Imię", max_length=50, required=False)
    last_name = forms.CharField(label="Nazwisko", max_length=50, required=False)
    email = forms.EmailField(label="Adres email", required=False)
    phone_number = forms.CharField(label="Numer telefonu", required=False)

    # Pola zgód przeniesione do formularza (nie bezpośrednio do modelu Rezerwations)

    regulations_consent = forms.BooleanField(
        label="Zapoznałem się z regulaminem oraz polityką prywatności.",
        required=True,
        help_text="Akceptacja regulaminu i polityki prywatności."
    )

    newsletter_consent = forms.BooleanField(
        label="Chcę zapisać się na newsletter, by otrzymywać informacje o przyszłych wydarzeniach i ofertach "
                    "specjalnych.",
        required=False,
        help_text="Warto zapisać się na newsletter",
    )


    class Meta:
        model = Rezerwations
        fields = [
            'participants_count',
            'type_of_payments',
        ]
        # event jest ustawiane automatycznie, więc nie jest w polach formularza

    def __init__(self, *args, **kwargs):
        # Pobierz zalogowanego użytkownika z kwargs
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Dodajemy hepltext do liczby uczestników, który będzie dynamicznie aktualizowany
        self.fields['participants_count'].help_text = "Podaj liczbę osób biorących udział w wydarzeniu."
        # Oznaczenie wymaganych zgód
        self.fields['regulations_consent'].required = True

        if self.user is not None and self.user.is_authenticated:
            for field in ['first_name', 'last_name', 'email', 'phone_number']:
                self.fields[field].widget = forms.HiddenInput()
                self.fields[field].required = True


    def clean(self):
        cleaned_data = super().clean()

        # Sprawdź czy mamy wystarczające dane do identyfikacji użytkownika
        if not self.user or not self.user.is_authenticated:
            # Sprawdź, czy podano wszystkie wymagane pola dla gościa
            for field in ['first_name', 'last_name', 'email', 'phone_number']:
                if not cleaned_data.get(field):
                    self.add_error(field, "To pole jest wymagane")

        # Weryfikacja obowiązkowych zgód
        if not cleaned_data.get('regulations_consent'):
            self.add_error('regulations_consent', 'Te zgody są wymagane do realizacji rezerwacji.')

        return cleaned_data


    def save(self, commit=True):
        instance = super().save(commit=False)

        if self.user and self.user.is_authenticated:
        # Dla zalogowanego użytkownika to na przyszłość
            instance.user = self.user
            instance.guest = None
        else:
            # Dla gościa - znajdź lub utwórz
            guest, created = GuestUser.objects.get_or_create(
                email=self.cleaned_data['email'],
                phone_number=self.cleaned_data['phone_number'],
                defaults={
                    'first_name': self.cleaned_data['first_name'],
                    'last_name': self.cleaned_data['last_name'],
                    'regulations_consent': self.cleaned_data['regulations_consent'],
                    'newsletter_consent': self.cleaned_data['newsletter_consent'],
                }
            )
            # Aktualizujemy zgody nawet jeśli użytkownik już istnieje

            if not created:
                guest.regulations_consent = self.cleaned_data['regulations_consent']
                guest.newsletter_consent = self.cleaned_data['newsletter_consent']
                guest.save()

            instance.guest = guest
            instance.user = None

        if commit:
            instance.save()

        return instance

