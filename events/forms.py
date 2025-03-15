from django import forms
from .models import Rezerwations


class RezerwationForm(forms.ModelForm):
    class Meta:
        model = Rezerwations
        fields = [
            'first_name', 'last_name', 'email', 'phone_number', 'type_of_payments',
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

