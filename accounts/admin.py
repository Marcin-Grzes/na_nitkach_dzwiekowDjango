from django.contrib import admin

from accounts.models import Customer


# Register your models here.

@admin.register(Customer)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['first_name',
                    'last_name',
                    'email',
                    'phone_number',
                    'regulations_consent',
                    'newsletter_consent',
                    'created_at',
                    ]
    search_fields = ['first_name',
                     'last_name',
                     'email',
                     'phone_number',
                     'newsletter_consent',
                     ]
    list_filter = ['regulations_consent',
                   'newsletter_consent',
                   'created_at',
                   ]
    date_hierarchy = 'created_at'

    fieldsets = [
        ('Dane osobowe', {
            'fields': ['first_name', 'last_name', 'email', 'phone_number']
        }),
        ('Zgody', {
            'fields': ['regulations_consent', 'newsletter_consent']
        }),
        ('Metadane', {
            'fields': ['created_at'],
            'classes': ['collapse']
        })
    ]

    readonly_fields = ['created_at']