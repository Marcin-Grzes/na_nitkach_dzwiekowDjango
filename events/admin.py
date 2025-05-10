from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from tinymce.widgets import TinyMCE

from .models import Rezerwations, EventType, EventImage, Events, Venue


# Register your models here.

class EventAdminForm(forms.ModelForm):
    description = forms.CharField(
        widget=TinyMCE(attrs={'cols': 80, 'rows': 30}),
        required=False
    )

    class Meta:
        model = EventType
        fields = '__all__'


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
    list_display = ['get_first_name', 'get_last_name', 'get_email', 'get_phone_number',
                    'event', 'status', 'participants_count', 'created_at',
                    'type_of_payments', 'created_at', 'get_regulations_consent', 'get_newsletter_consent',
                    'consent_status']

    # Metody do pobierania danych użytkownika
    def get_first_name(self, obj):
        if obj.user:
            return obj.user.first_name
        elif obj.guest:
            return obj.guest.first_name
        return None
    get_first_name.short_description = 'Imię'


    def get_last_name(self, obj):
        if obj.user:
            return obj.user.last_name
        elif obj.guest:
            return obj.guest.last_name
        return None
    get_last_name.short_description = "Nazwisko"

    def get_email(self, obj):
        if obj.user:
            return obj.user.email
        elif obj.guest:
            return obj.guest.email
        return None
    get_email.short_description = "Email"

    def get_phone_number(self, obj):
        if obj.user:
            return obj.user.phone_number
        elif obj.guest:
            return obj.guest.phone_number
    get_phone_number.short_description = "Telefon"

    def get_regulations_consent(self, obj):
        if obj.user:
            return obj.user.profile.regulations_consent
        elif obj.guest:
            return obj.guest.regulations_consent
        return None

    get_regulations_consent.short_description = "Akceptacja regulaminu i polityki prywatności"
    get_regulations_consent.boolean = True # wyświetla True/False jako ✓/✗

    def get_newsletter_consent(self, obj):
        if obj.user:
            return obj.user.profile.newsletter_consent
        elif obj.guest:
            return obj.guest.newsletter_consent
        return None
    get_newsletter_consent.short_description = "Newsletter"
    get_regulations_consent.boolean = True

    # Kolumny, które po kliknięciu prowadzą do edycji
    list_display_links = ['get_first_name', 'get_last_name']

    # Pola do wyszukiwania
    search_fields = ['guest_first_name', 'guest_last_name', 'guest_email', 'guest_phone_number']

    # Filtrowanie boczne
    list_filter = ['type_of_payments', 'created_at', 'status', 'event', 'created_at']

    actions = ['confirm_reservations', 'move_to_waitlist', 'cancel_reservations']

    # Domyślne sortowanie
    ordering = ['-created_at']

    # Pola tylko do odczytu w edycji
    readonly_fields = ['created_at']

    # Grupy pól w formularzu edycji
    fieldsets = [
        ('Wydarzenie i status', {
            'fields': ('event', 'status')
        }),
        ('Powiązania użytkowników', {
            'fields': ['guest', 'user']
        }),
        ('Liczba uczestników',{
            'fields': ['participants_count']
        }),
        ('Informacje o płatności', {
            'fields': ['type_of_payments']
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

    # Zmieniona implementacja consent_status
    def consent_status(self, obj):
        if obj.user:
            return '✓' if obj.user.profile.newsletter_consent else '✗'
        elif obj.guest:
            return '✓' if obj.guest.newsletter_consent else '✗'
        return '?'

    consent_status.short_description = 'Marketing'

    def confirm_reservations(self, request, queryset):
        updated = queryset.update(status=Rezerwations.ReservationStatus.CONFIRMED, waitlist_position=None)
        self.message_user(request, f"{updated} rezerwacji zostało potwierdzonych.")

    confirm_reservations.short_description = "Potwierdź wybrane rezerwacje"

    def move_to_waitlist(self, request, queryset):
        # Dla każdej rezerwacji obliczamy pozycję na liście rezerwowej
        for reservation in queryset:
            if reservation.status != Rezerwations.ReservationStatus.WAITLIST:
                reservation.status = Rezerwations.ReservationStatus.WAITLIST
                reservation.waitlist_position = reservation.event.get_next_waitlist_position()
                reservation.save()

        self.message_user(request, f"{queryset.count()} rezerwacji przeniesionych na listę rezerwową.")

    move_to_waitlist.short_description = "Przenieś wybrane rezerwacje na listę rezerwową"

    def cancel_reservations(self, request, queryset):
        # Używamy metody cancel dla każdej rezerwacji
        count = 0
        waitlist_promotions = 0

        for reservation in queryset:
            if reservation.cancel():
                count += 1
                # Sprawdź czy spowodowało to przesunięcie z listy rezerwowej
                if reservation.event.reservations.filter(
                        status=Rezerwations.ReservationStatus.CONFIRMED,
                        waitlist_position__isnull=True
                ).exists():
                    waitlist_promotions += 1

        message = f"{count} rezerwacji zostało anulowanych."
        if waitlist_promotions > 0:
            message += f" {waitlist_promotions} osób z listy rezerwowej zostało automatycznie potwierdzonych."

        self.message_user(request, message)

    cancel_reservations.short_description = "Anuluj wybrane rezerwacje"


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
    form = EventAdminForm
    list_display = ['title', 'type_of_events', 'start_datetime', 'end_datetime',
                    'venue','price', 'max_participants', 'get_available_seats', 'is_active']
    list_filter = ['type_of_events', 'is_active', 'venue']
    search_fields = ['title', 'description']
    date_hierarchy = 'start_datetime'
    inlines = [EventImageInline]
    autocomplete_fields = ['venue', 'type_of_events']  # Dodane pole autocomplete
    actions = ['duplicate_event']


    # Opcjonalnie, jeśli chcesz dostosować edytor do konkretnego pola w panelu administracyjnym:

    # formfield_overrides = {
    #     models.TextField: {'widget': TinyMCE()},
    # }

    # Alternatywnie, możesz też nadpisać tylko konkretne pole:
    # def formfield_for_dbfield(self, db_field, **kwargs):
    #     if db_field.name == 'description':
    #         kwargs['widget'] = TinyMCE(attrs={'cols': 80, 'rows': 30})
    #     return super().formfield_for_dbfield(db_field, **kwargs)

    # Dodanie pól ze statystykami rezerwacji jako pola tylko do odczytu
    readonly_fields = [
        'reserved_seats_display',
        'available_seats_display',
        'waitlist_count_display',
    ]
    class Media:
        js = ('admin/js/admin_enhancements.js',)

    fieldsets = [
        ('Podstawowe informacje', {
            'fields': ['title', 'type_of_events', 'description', 'main_image', 'price']
        }),
        ('Czas i miejsce', {
            'fields': ['start_datetime', 'end_datetime', 'venue']
        }),
        ('Ustawienia uczestników', {
            'fields': [
                'max_participants',
                'reservation_end_time',
                'reserved_seats_display',
                'available_seats_display',
                'waitlist_count_display',
            ]
        }),
        ('Status', {
            'fields': ['is_active']
        }),
    ]

    # Metody do wyświetlania statystyk rezerwacji
    def reserved_seats_display(self, obj):
        reserved = obj.get_confirmed_reservations_count()
        max_seats = obj.max_participants
        percentage = round((reserved / max_seats) * 100) if max_seats > 0 else 0

        # Formatowanie HTML z kolorami w zależności od wypełnienia
        color = "black"
        # if percentage > 75:
        #     color = "orange"
        # if percentage >= 100:
        #     color = "red"

        return format_html(
            '<div style="font-weight: bold; color: {};">{} z {} miejsc ({} %)</div>',
            color, reserved, max_seats, percentage
        )

    reserved_seats_display.short_description = "Zajęte miejsca"

    def available_seats_display(self, obj):
        available = obj.get_available_seats()
        max_seats = obj.max_participants
        percentage = round((available / max_seats) * 100) if max_seats > 0 else 0

        # Formatowanie HTML z kolorami w zależności od dostępności
        color = "black"
        # if percentage < 25:
        #     color = "orange"
        # if percentage <= 0:
        #     color = "red"

        return format_html(
            '<div style="font-weight: bold; color: {};">{} dostępnych miejsc ({} %)</div>',
            color, available, percentage
        )

    available_seats_display.short_description = "Dostępne miejsca"

    def waitlist_count_display(self, obj):
        waitlist_count = obj.get_waitlist_count()

        if waitlist_count == 0:
            return format_html('<div style="color: black;">Brak osób na liście rezerwowej</div>')
        else:
            return format_html(
                '<div style="font-weight: bold; color: black;">{} osób oczekujących</div>',
                waitlist_count
            )

    waitlist_count_display.short_description = "Lista rezerwowa"

    def duplicate_event(self, request, queryset):
        """
        Akcja administratora pozwalająca na tworzenie duplikatów wybranych wydarzeń.
        """
        # Możemy duplikować tylko jedno wydarzenie na raz
        if queryset.count() != 1:
            self.message_user(
                request,
                "Proszę wybrać dokładnie jedno wydarzenie do duplikowania.",
                level=messages.ERROR
            )
            return

        # Pobieramy oryginalne wydarzenie
        original_event = queryset.first()
        # Tworzymy nowy obiekt wydarzenie bez zapisywania go w bazie
        new_event = Events(
            title=f"Kopia - {original_event.title}",
            type_of_events=original_event.type_of_events,
            start_datetime=original_event.start_datetime,
            end_datetime=original_event.end_datetime,
            venue=original_event.venue,
            price=original_event.price,
            max_participants=original_event.max_participants,
            description=original_event.description,
            is_active=original_event.is_active
        )

        # Jeśli wydarzenie ma główne zdjęcie, kopiujemy je
        if original_event.main_image:
            # Plik zostanie skopiowany przy zapisie
            new_event.main_image = original_event.main_image

        # Zapisujemy nowe wydarzenie w bazie danych
        new_event.save()

        # Kopiujemy powiązane zdjęcia
        for image in original_event.images.all():
            EventImage.objects.create(
                event=new_event,
                image=image.image,  # Plik będzie skopiowany przy zapisie
                caption=image.caption,
                order=image.order
            )

        # Wyświetl komunikat o sukcesie
        self.message_user(
            request,
            f"Wydarzenie '{original_event.title}' zostało zduplikowane jako '{new_event.title}'.",
            level=messages.SUCCESS
        )

        # Przekierowujemy do strony edycji nowego wydarzenia
        return HttpResponseRedirect(
            reverse('admin:events_events_change', args=[new_event.id])
        )

    duplicate_event.short_description = "Duplikuj wybrane wydarzenie"

    def save_model(self, request, obj, form, change):
        try:
            obj.full_clean()  # Wykonaj pełną walidację
            super().save_model(request, obj, form, change)
        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    form.add_error(field, error)
