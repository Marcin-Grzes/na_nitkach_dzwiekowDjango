from django.contrib import admin


class MetadataAdminModel(admin.ModelAdmin):
    """
    Rozszerzona klasa ModelAdmin z obsługą metadanych.
    Wszystkie klasy admin mogą po niej dziedziczyć.
    """

    def get_readonly_fields(self, request, obj=None):
        """Dodaje pola metadanych do readonly_fields"""
        readonly_fields = list(super().get_readonly_fields(request, obj) or [])
        metadata_fields = ['created_at', 'updated_at', 'created_ip', 'updated_ip']

        for field in metadata_fields:
            if field in readonly_fields:
                readonly_fields.append(field)

        return readonly_fields

    def get_fields(self, request, obj=None):
        """Dodaje sekcję metadanych do fieldsets, jeśli nie istnieje"""
        fieldsets = list(super().get_fieldsets(request, obj))

        # Sprawdź, czy istnieje sekcja metadanych
        has_metadata_section = any(name == 'Metadane' for name, _ in fieldsets)

        # Jeśli nie ma sekcji metadanych, dodaj ją
        if not has_metadata_section:
            metadata_fields = ['created_at', 'updated_at', 'created_by_admin', 'created_ip', 'updated_ip']
            fieldsets.append(('Metadane', {
                'fields': metadata_fields,
                'classes': ['collapse']
            }))

        return fieldsets

    def save_model(self, request, obj, form, change):
        """Dodaje metadane administratora przed zapisaniem modelu"""
        if not change:  # Jeśli tworzymy nowy obiekt
            obj.created_by_admin = True
            obj.created_ip = self.get_client_ip(request)
        else:  # Jeśli aktualizujemy obiekt
            obj.updated_ip = self.get_client_ip(request)

        super().save_model(request, obj, form, change)

    def get_client_ip(self, request):
        """Pobiera adres IP z żądania"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
