from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from tinymce.widgets import TinyMCE
from accounts.admin_base import MetadataAdminModel

from accounts import models
from .models import Reservations, EventType, EventImage, Events, Venue
from .views import ReservationEmailMixin


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


@admin.register(Reservations)
class ReservationsAdmin(ReservationEmailMixin, MetadataAdminModel):
    change_list_template = '../templates/admin/change_list.html'

    """Wyświetlane kolumny na liście"""

    list_display = ['get_customer_name', 'customer_email', 'customer_phone_number',
                    'event', 'status', 'participants_count', 'created_at',
                    'type_of_payments', 'created_at', 'get_newsletter_consent',
                    'updated_at', 'created_by_admin', 'created_ip', 'updated_ip',
                    ]

    """Metody pomocnicze:"""

    def save_model(self, request, obj, form, change):
        """
        Metoda wywoływana przy zapisie modelu w panelu administratora.
        Wykrywa zmiany statusu i utworzenie nowej rezerwacji i wysyła odpowiednie powiadomienia e-mail.
        """

        # Zapisanie oryginalnego stanu przed zapisem, jeśli obiekt juz istnieje
        if change and obj.pk:
            old_obj = Reservations.objects.get(pk=obj.pk)
            old_status = old_obj.status
        else:
            old_status = None

        # Wywołanie standardowej metody zapisu
        super().save_model(request, obj, form, change)

        # Przypadek 1: Nowa rezerwacja utworzona przez administratora
        if not change:
            # Wysłanie odpowiedniego powiadomienia w zależności od statusu nowej rezerwacji
            if obj.status == Reservations.ReservationStatus.CONFIRMED:
                self.send_email(obj, 'confirmation')
                self.message_user(request, f"Utworzono nową rezerwację. Wysłano powiadomienie do {obj.customer.email}.")
            elif obj.status == Reservations.ReservationStatus.WAITLIST:
                self.send_email(obj, 'confirmation')  # Używamy tego samego szablonu
                self.message_user(request,
                                  f"Utworzono nową rezerwację na liście rezerwowej. Wysłano powiadomienie do {obj.customer.email}.")

        # Przypadek 2: Zmiana statusu istniejącej rezerwacji
        elif old_status != obj.status:
            # Wysłanie odpowiedniego powiadomienia w zależności od nowego statusu
            if obj.status == Reservations.ReservationStatus.CONFIRMED:
                self.send_email(obj, 'confirmation')
            elif obj.status == Reservations.ReservationStatus.WAITLIST:
                self.send_email(obj, 'confirmation')  # Używamy tego samego szablonu dla listy rezerwowej
            elif obj.status == Reservations.ReservationStatus.CANCELLED:
                self.send_email(obj, 'cancellation')

    def get_customer_name(self, obj):
        return obj.customer.get_full_name() if obj.customer else '-'

    get_customer_name.short_description = 'Imię i nazwisko'

    def customer_email(self, obj):
        return obj.customer.email if obj.customer else '-'

    customer_email.short_description = 'Email'

    def customer_phone_number(self, obj):
        return obj.customer.phone_number if obj.customer else '-'

    customer_phone_number.short_description = 'Numer telefonu'

    def get_newsletter_consent(self, obj):
        return obj.customer.newsletter_consent if obj.customer else False

    get_newsletter_consent.short_description = 'Newsletter'
    get_newsletter_consent.boolean = True

    def changelist_view(self, request, extra_context=None):
        """Dodaje sumę uczestników dla wyfiltrowanych rezerwacji"""
        response = super().changelist_view(request, extra_context)

        # Sprawdź czy jest widok zmiany listy z wynikami
        if hasattr(response, 'context_data') and 'cl' in response.context_data:
            cl = response.context_data['cl']
            queryset = cl.queryset

            # Jeśli mamy wyniki po filtrowaniu
            if queryset is not None:
                # Oblicz sumę uczestników
                total_participants = queryset.aggregate(
                    total_participants=Sum('participants_count')
                )['total_participants'] or 0

                # Dodaj do kontekstu
                response.context_data['total_participants'] = total_participants

                # Jeśli filtrujemy po evencie, dodaj nazwę
                event_id = request.GET.get('event__id__exact')
                if event_id:
                    try:
                        event = Events.objects.get(id=event_id)
                        response.context_data['filtered_event'] = event
                    except Events.DoesNotExist:
                        pass
        return response

    # Kolumny, które po kliknięciu prowadzą do edycji
    # list_display_links = ['first_name', 'last_name']

    # Pola do wyszukiwania
    search_fields = ['customer__first_name',
                     'customer__last_name',
                     'customer__email',
                     'customer__phone_number',
                     ]

    # Filtrowanie boczne
    list_filter = ['type_of_payments',
                   #'customer__regulations_consent', django krzyczy ze mu nie pasuje
                   #'customer__newsletter_consent', j.w
                   'created_at', 'status',
                   'event']

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
        ('Klient', {
            'fields': ['customer']
        }),
        ('Liczba uczestników', {
            'fields': ['participants_count']
        }),
        ('Informacje o płatności', {
            'fields': ['type_of_payments']
        }),
        # ('Metadane', {
        #     'fields': ['created_at', 'updated_at', 'created_by_admin', 'created_ip', 'updated_ip'],
        #     'classes': ['collapse']  # zwijana sekcja
        # }),
    ]

    autocomplete_fields = ['event', 'customer']  #'customer' było w środku ale Django krzyczy ze mu nie pasuje.

    # Niestandardowe wyświetlanie pól
    def payment_display(self, obj):
        return obj.get_type_of_payments_display()

    payment_display.short_description = 'Sposób płatności'

    def consent_status(self, obj):
        return '✓' if obj.newsletter_consent else '✗'

    def confirm_reservations(self, request, queryset):
        updated = queryset.update(status=Reservations.ReservationStatus.CONFIRMED, waitlist_position=None)

        for reservation in queryset:
            # Odświeżamy obiekt, aby uzyskać zaktualizowane dane
            reservation.refresh_from_db()
            if reservation.status == Reservations.ReservationStatus.CONFIRMED:
                self.send_email(reservation, 'confirmation')

        self.message_user(request, f"{updated} rezerwacji zostało potwierdzonych.")

    confirm_reservations.short_description = "Potwierdź wybrane rezerwacje"

    def move_to_waitlist(self, request, queryset):
        """Przenosi wybrane rezerwacje na listę rezerwową i wysyła powiadomienia"""
        # Dla każdej rezerwacji obliczamy pozycję na liście rezerwowej
        count = 0

        for reservation in queryset:
            if reservation.status != Reservations.ReservationStatus.WAITLIST:
                reservation.status = Reservations.ReservationStatus.WAITLIST
                reservation.waitlist_position = reservation.event.get_next_waitlist_position()
                reservation.save()

                # Wysyłanie e-maila z informacją o dodaniu do listy rezerwowej
                self.send_email(reservation, 'confirmation')
                count += 1

        self.message_user(request, f"{queryset.count()} rezerwacji przeniesionych na listę rezerwową.")

    move_to_waitlist.short_description = "Przenieś wybrane rezerwacje na listę rezerwową"

    def cancel_reservations(self, request, queryset):
        """Anuluje wybrane rezerwacje, aktualizuje listę rezerwową i wysyła powiadomienia"""
        # Używamy metody cancel dla każdej rezerwacji
        count = 0
        waitlist_promotions = 0

        for reservation in queryset:
            original_status = reservation.status
            if reservation.cancel():
                count += 1

                # Wysyłanie e-maila o anulowaniu rezerwacji
                self.send_email(reservation, 'cancellation')

                # Sprawdzanie czy nastąpiło przesunięcie z listy rezerwowej
                if original_status == Reservations.ReservationStatus.CONFIRMED:
                    promoted_reservations = reservation.event.reservations.filter(
                        status=Reservations.ReservationStatus.CONFIRMED,
                        waitlist_position__isnull=True
                    ).exclude(id=reservation.id)

                    # Uwaga: powiadomienia dla osób z listy rezerwowej są już wysyłane
                    # przez funkcję cancel_reservation poprzez wywołanie send_waitlist_promotion_email
                    waitlist_promotions += promoted_reservations.count()

        message = f"{count} rezerwacji zostało anulowanych i wysłano powiadomienia."
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
class EventsAdmin(MetadataAdminModel):
    form = EventAdminForm
    list_display = ['title', 'type_of_events', 'start_datetime', 'end_datetime',
                    'venue', 'price', 'max_participants', 'get_available_seats', 'is_active']
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
        'waitlist_participants_count',
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
                'waitlist_participants_count',
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

    def waitlist_participants_count(self, obj):
        waitlist_count = obj.get_waitlist_participants_count()

        if waitlist_count == 0:
            return format_html('<div style="color: black;">Brak osób na liście rezerwowej</div>')
        else:
            return format_html(
                '<div style="font-weight: bold; color: black;">{} osób oczekujących</div>',
                waitlist_count
            )

    waitlist_participants_count.short_description = "Lista rezerwowa"

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
