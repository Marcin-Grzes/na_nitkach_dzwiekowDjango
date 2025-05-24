from django.utils import timezone

from django import forms
from .models import Reservations, Events, EventType, Venue
from accounts.models import Customer


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
    Łączy dane klienta i rezerwacji
    """

    website_url = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        label='Leave empty'
    )

    """Pola dla modelu Customer"""
    first_name = forms.CharField(label="Imię", max_length=50)
    last_name = forms.CharField(label="Nazwisko", max_length=50)
    email = forms.EmailField(label="Adres email")
    phone_number = forms.CharField(label="Numer telefonu")
    regulations_consent = forms.BooleanField(
        label="Akceptacja regulaminu i polityki prywatności.",
        required=True,
        help_text="Akceptuję regulamin i politykę prywatności."
    )
    newsletter_consent = forms.BooleanField(
        label="Zapisz mnie na newsletter.",
        required=False,
        help_text="Chcę zapisać się newsletter, by otrzymywać informacje o przyszłych wydarzeniach wydarzeniach"
                  " i ofertach specjalnych."
    )

    class Meta:
        model = Reservations
        fields = [
            'participants_count',
            'type_of_payments',
        ]
        # event jest ustawiane automatycznie, więc nie jest w polach formularza

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dodajemy hepltext do liczby uczestników, który będzie dynamicznie aktualizowany
        self.fields['participants_count'].help_text = "Podaj liczbę osób biorących udział w wydarzeniu."
        # Oznaczenie wymaganych zgód
        # self.fields['regulations_consent'].required = True

    def clean(self):
        cleaned_data = super().clean()

        # Weryfikacja obowiązkowych zgód
        if not cleaned_data.get('regulations_consent'):
            self.add_error('regulations_consent', 'Ta zgoda jest wymagana do realizacji rezerwacji.')

        return cleaned_data

    def clean_website_url(self):
        """Walidacja pola honeypot"""
        value = self.cleaned_data.get('website_url', '')
        if value:
            raise forms.ValidationError('Wykryto automatyczne wypełnianie formularza.')
        return value


class UniversalReservationForm(forms.ModelForm):

    """ Uniwersalny formularz z możliwością wyboru wydarzenia z listy """

    # Dodaj pole honeypot
    website_url = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        label='Leave empty'
    )

    event = forms.ModelChoiceField(
        queryset=Events.objects.none(), # # Pusty queryset, będzie aktualizowany w __init__
        label="Wybierz wydarzenie",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'event-selector'}),
    )

    """ Pozostałe pola jak w EventReservationForm """

    first_name = forms.CharField(label="Imię", max_length=50)
    last_name = forms.CharField(label="Nazwisko", max_length=50)
    email = forms.EmailField(label="Adres email")
    phone_number = forms.CharField(label="Numer telefonu")
    regulations_consent = forms.BooleanField(
        label="Akceptacja regulaminu i polityki prywatności.",
        required=True,
        help_text="Akceptuję regulamin i politykę prywatności."
    )
    newsletter_consent = forms.BooleanField(
        label="Zapisz mnie na newsletter.",
        required=False,
        help_text="Chcę zapisać się newsletter, by otrzymywać informacje o przyszłych wydarzeniach wydarzeniach"
                  " i ofertach specjalnych."
    )

    class Meta:
        model = Reservations
        fields = [
            'event',
            'participants_count',
            'type_of_payments',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ustaw queryset dla aktywnych przyszłych wydarzeń
        self.fields['event'].queryset = Events.objects.filter(
            is_active=True,
            start_datetime__gte=timezone.now()
        ).order_by('start_datetime')

        self.fields['participants_count'].help_text = "Podaj liczbę osób biorących udział w wydarzeniu."

    def clean(self):
        cleaned_data = super().clean()

        # Weryfikacja obowiązkowych zgód
        if not cleaned_data.get('regulations_consent'):
            self.add_error('regulations_consent', 'Ta zgoda jest wymagana do realizacji rezerwacji.')

        return cleaned_data

    def clean_website_url(self):
        """Walidacja pola honeypot"""
        value = self.cleaned_data.get('website_url', '')
        if value:
            raise forms.ValidationError('Wykryto automatyczne wypełnianie formularza.')
        return value