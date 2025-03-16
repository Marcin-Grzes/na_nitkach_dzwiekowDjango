from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import Rezerwations, EventType, EventImage, Events, Venue


# Register your models here.

class EventImageInline(admin.TabularInline):
    model = EventImage
    extra = 1  # liczba pustych formularzy do wyświetlenia
    fields = ['image', 'caption', 'order']


class EventInline(admin.TabularInline):
    model = Events
    fields = ['title', 'start_datetime', 'end_datetime', 'is_active']
    extra = 0
    show_change_link = True
    can_delete = False
    readonly_fields = ['title', 'start_datetime', 'end_datetime', 'is_active']

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Rezerwations)
class RezerwationsAdmin(admin.ModelAdmin):
    # Wyświetlane kolumny na liście
    list_display = ['first_name', 'last_name', 'email', 'phone_number',
                    'type_of_payments', 'created_at', 'marketing_emails_consent', 'reminder_emails_consent',
                    'consent_status']

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

    # Niestandardowe wyświetlanie pól
    def payment_display(self, obj):
        return obj.get_type_of_payments_display()

    payment_display.short_description = 'Sposób płatności'

    def consent_status(self, obj):
        return '✓' if obj.marketing_emails_consent else '✗'

    consent_status.short_description = 'Marketing'

    def colored_type_of_payments(self, obj):
        if obj.type_of_payments == 'blik':
            return format_html(
                '<span style="background-color: #90EE90; padding: 3px 10px; border-radius: 5px;">BLIK</span>')
        else:
            return format_html(
                '<span style="background-color: #FFD580; padding: 3px 10px; border-radius: 5px;">Gotówka</span>')

    colored_type_of_payments.short_description = 'Płatność'

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


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'city', 'postal_code']
    list_filter = ['city']
    search_fields = ['name', 'address', 'city', 'postal_code']  # Ważne dla autocomplete
    readonly_fields = ['map_preview']
    inlines = [EventInline]

    fieldsets = [
        ('Podstawowe informacje', {
            'fields': ['name', 'city', 'address', 'postal_code']
        }),
        ('Informacje dodatkowe', {
            'fields': ['additional_info'],
            'classes': ['collapse']  # Możliwość zwijania tej sekcji
        }),
        ('Mapa', {
            'fields': ['map_iframe', 'map_preview'],
        }),
    ]

    def map_preview(self, obj):
        if obj.map_iframe:
            return mark_safe(obj.map_iframe)
        return "Brak mapy do wyświetlenia"

    map_preview.short_description = "Podgląd mapy"


@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    list_filter = ['is_active']


@admin.register(EventImage)
class EventImageAdmin(admin.ModelAdmin):
    list_display = ['event', 'caption', 'order']
    list_filter = ['event']
    search_fields = ['caption', 'event__title']


@admin.register(Events)
class EventsAdmin(admin.ModelAdmin):
    list_display = ['title', 'type_of_events', 'start_datetime', 'end_datetime',
                    'venue', 'max_participants', 'get_available_seats', 'is_active']
    list_filter = ['type_of_events', 'is_active', 'venue']
    search_fields = ['title', 'description']
    date_hierarchy = 'start_datetime'
    inlines = [EventImageInline]
    autocomplete_fields = ['venue', 'type_of_events']  # Dodane pole autocomplete

    class Media:
        js = ('admin/js/admin_enhancements.js',)

    fieldsets = [
            ('Podstawowe informacje', {
                'fields': ['title', 'type_of_events', 'description', 'main_image']
            }),
            ('Czas i miejsce', {
                'fields': ['start_datetime', 'end_datetime', 'venue']
            }),
            ('Ustawienia uczestników', {
                'fields': ['max_participants']
            }),
            ('Status', {
                'fields': ['is_active']
            }),
        ]

    def save_model(self, request, obj, form, change):
        try:
            obj.full_clean()  # Wykonaj pełną walidację
            super().save_model(request, obj, form, change)
        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    form.add_error(field, error)
