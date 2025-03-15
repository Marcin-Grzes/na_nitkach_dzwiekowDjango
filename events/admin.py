from django.contrib import admin
from .models import Rezerwations
# Register your models here.

@admin.register(Rezerwations)
class RezerwationsAdmin(admin.ModelAdmin):
    # Wyświetlane kolumny na liście
    list_display = ['first_name', 'last_name', 'email', 'phone_number',
                    'type_of_payments', 'created_at', 'marketing_emails_consent', 'reminder_emails_consent']

    # Kolumny, które po kliknięciu prowadzą do edycji
    list_display_links = ['first_name', 'last_name']

    # Pola do wyszukiwania
    search_fields = ['first_name', 'last_name', 'email', 'phone_number']

    # Filtrowanie boczne
    list_filter = ['type_of_payments', 'data_processing_consent',
                   'privacy_policy_consent', 'marketing_emails_consent', 'created_at', 'reminder_emails_consent']

    # Domyślne sortowanie
    ordering = ['-created_at']

    # Pola tylko do odczytu w edycji
    readonly_fields = ['created_at']

    # Grupy pól w formularzu edycji
    fieldsets = [
        ('Dane osobowe', {
            'fields': ['first_name', 'last_name', 'email', 'phone_number']
        }),
        ('Informacje o płatności', {
            'fields': ['type_of_payments']
        }),
        ('Zgody', {
            'fields': ['data_processing_consent', 'privacy_policy_consent',
                       'marketing_emails_consent', 'reminder_emails_consent']
        }),
        ('Metadane', {
            'fields': ['created_at'],
            'classes': ['collapse']  # zwijana sekcja
        }),
    ]

    # Eksport do CSV (opcjonalnie)
    actions = ['export_to_csv']

    def export_to_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="rezerwacje.csv"'

        writer = csv.writer(response)
        writer.writerow(['Imię', 'Nazwisko', 'Email', 'Telefon', 'Płatność'])

        for obj in queryset:
            writer.writerow([
                obj.first_name,
                obj.last_name,
                obj.email,
                obj.phone_number,
                obj.get_type_of_payments_display()
            ])

        return response

    export_to_csv.short_description = "Eksportuj wybrane do CSV"