from django.contrib import admin
from django.utils.html import format_html

from accounts.admin_base import MetadataAdminModel
from accounts.models import Customer
from events.models import Reservations


# Register your models here.

class CustomerReservationInline(admin.TabularInline):
    model = Reservations
    extra = 0  # Brak dodatkowych pustych formularzy
    readonly_fields = ['event_info', 'status', 'participants_count', 'type_of_payments', 'created_at']
    fields = ['event_info', 'status', 'participants_count', 'type_of_payments', 'created_at']
    can_delete = False # Nie można usuwać rezerwacji z tego widoku
    show_change_link = True # Dodaje link do edycji rezerwacji

    def event_info(self, obj):
        if obj.event_info:
            return format_html(
                '<strong>{}</strong><br/>{}<br/>{}',
                obj.event.title,
                obj.event.start_datetime.strftime('%d.%m.%Y %H:%M'),
                obj.event.venue.name if obj.event.venue else ''
            )
            return "-"
    event_info.short_description = "Wydarzenie (nazwa, data, miejsce)"

    def has_add_permission(self, request, obj=None):
        return False  # Nie można dodawać rezerwacji z tego widoku



@admin.register(Customer)
class CustomUserAdmin(MetadataAdminModel):
    list_display = ['first_name',
                    'last_name',
                    'email',
                    'phone_number',
                    'regulations_consent',
                    'newsletter_consent',
                    'created_at',
                    'created_by_admin',
                    ]
    search_fields = ['first_name',
                     'last_name',
                     'email',
                     'phone_number',
                     'newsletter_consent',
                     'created_by_admin',
                     ]
    list_filter = ['regulations_consent',
                   'newsletter_consent',
                   'created_at',
                   'created_by_admin',
                   ]
    date_hierarchy = 'created_at'

    fieldsets = [
        ('Dane osobowe', {
            'fields': ['first_name', 'last_name', 'email', 'phone_number']
        }),
        ('Zgody', {
            'fields': ['regulations_consent', 'newsletter_consent']
        }),
    ]

    readonly_fields = ['created_at']
    inlines = [CustomerReservationInline]