from django.contrib import admin

from accounts.admin_base import MetadataAdminModel
from accounts.models import Customer


# Register your models here.

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