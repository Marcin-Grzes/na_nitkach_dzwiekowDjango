from django import forms
from .models import Rezerwations, Events, EventType, Venue

class RezerwationForm(forms.ModelForm):
    class Meta:
        model = Rezerwations
        fields = [
            'first_name', 'last_name', 'email', 'participants_count', 'phone_number', 'type_of_payments',
            'data_processing_consent', 'privacy_policy_consent', 'marketing_emails_consent', 'reminder_emails_consent'
        ]

    def clean(self):
        cleaned_data = super().clean()

        # Weryfikacja obowiązkowych zgód (przykład)
        if not cleaned_data.get('data_processing_consent'):
            self.add_error('data_processing_consent', 'Ta zgoda jest wymagana do realizacji rezerwacji.')

        if not cleaned_data.get('privacy_policy_consent'):
            self.add_error('privacy_policy_consent', 'Akceptacja polityki prywatności jest wymagana.')

        return cleaned_data


class EventForm(forms.ModelForm):
    class Meta:
        model = Events
        fields = [
            'title', 'type_of_events', 'start_datetime', 'end_datetime',
            'venue', 'max_participants', 'description', 'main_image', 'is_active'
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

