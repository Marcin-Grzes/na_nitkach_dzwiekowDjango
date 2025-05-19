import json

from django.contrib.admin.views.decorators import staff_member_required
from django.db import IntegrityError

from django.http import JsonResponse
from django.utils import timezone
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.utils.html import strip_tags
from django.views import View
from django.urls import reverse
from django.views.generic import ListView, DetailView
from django.views.generic.base import ContextMixin, TemplateView
from honeypot.decorators import check_honeypot

from accounts.models import Customer
from events.forms import EventReservationForm, UniversalReservationForm
from django.contrib import messages
from events.models import EventType, Events, Reservations
from events.services import cancel_reservation


# Create your views here.

class HomeView(View):
    def get(self, request):
        return render(request, 'index.html')


class Base(View):
    def get(self, request):
        return render(request, '404.html')


class TestCalendar(View):
    def get(self, request):
        return render(request, 'events/test_calendar.html')


class ReservationSuccessView(View):
    """
    Widok potwierdzenia rezerwacji wyświetlany po pomyślnym dokonaniu rezerwacji.
    """

    def get(self, request, event_id, reservation_id):
        # Pobierz wydarzenie i rezerwację
        event = get_object_or_404(Events, id=event_id, is_active=True)
        reservation = get_object_or_404(Reservations, id=reservation_id)

        # Sprawdź czy rezerwacja należy do tego wydarzenia
        if reservation.event.id != event.id:
            messages.error(request, "Wystąpił błąd. Nieprawidłowe dane rezerwacji.")
            return redirect('event_detail', event_id=event_id)

        context = {
            'event': event,
            'reservation': reservation,
        }

        return render(request, 'reservation_success.html', context)


class ReservationEmailMixin:
    """Mixin dostarczający metody wysyłania emaili dla widoków rezerwacji"""

    def send_email(self, reservation, email_type):
        """
        Wysyła e-mail związany z rezerwacją.
         Parametry:
        - reservation: obiekt rezerwacji
        - email_type: typ emaila - 'confirmation', 'cancellation', 'waitlist_promotion'
        """

        email_types = {
            'confirmation': {
                'subject': f'Potwierdzenie rezerwacji - {reservation.event.title}',
                'template': 'mail/mail_event_reservation_confirmation.html',
            },
            'cancellation': {
                'subject': f'Anulowanie rezerwacji - {reservation.event.title}',
                'template': 'mail/mail_event_reservation_confirmation.html',
            },
        }

        # Sprawdź czy żądany typ emaila jest obsługiwany

        if email_type not in email_types:
            raise ValueError(f'Nieobsługiwany typ emaila {email_type}')

        email_config = email_types[email_type]

        context = {
            'first_name': reservation.customer.first_name,
            'last_name': reservation.customer.last_name,
            'participants_count': reservation.participants_count,
            'email': reservation.customer.email,
            'phone_number': str(reservation.customer.phone_number),
            'payment_method': reservation.get_type_of_payments_display(),
            'event': reservation.event,
            'reservation': reservation,
        }

        html_message = render_to_string(email_config['template'], context)
        plain_message = strip_tags(html_message)

        send_mail(
            email_config['subject'],
            plain_message,
            None,  # używa DEFAULT_FROM_EMAIL z ustawień
            [reservation.customer.email],
            html_message=html_message,
        )


class EventReservationView(ReservationEmailMixin, View):
    """
    Widok do rezerwacji miejsc na konkretne wydarzenie.
    Przyjmuje ID wydarzenia z URL i tworzy odpowiednią rezerwację.
    """

    # @check_honeypot
    def get(self, request, event_id):
        # Pobierz wydarzenie lub zwróć 404
        event = get_object_or_404(Events, id=event_id, is_active=True)

        # Sprawdź dostępność rezerwacji (mimo że będziemy to sprawdzać dynamicznie przez JS)
        reservation_available = event.is_reservation_available()

        # Sprawdź czy są jeszcze miejsca
        if event.is_fully_booked():
            messages.warning(
                request,
                "Wszystkie miejsca na to wydarzenie są już zajęte. Możesz zapisać się na listę rezerwową."
            )

        # Tworzenie formularza pre-konfigurowanego dla tego wydarzenia
        form = EventReservationForm(initial={'event': event})  #??

        context = {
            'form': form,
            'event': event,
            'reservation_available': reservation_available
        }

        # Dodajemy formatowanie czasu dla JavaScript
        if event.reservation_end_time:
            context['reservation_end_time_iso'] = event.reservation_end_time.isoformat()

        return render(request, 'event_reservation_form.html', context)

    # @check_honeypot
    def post(self, request, event_id):
        # Pobierz wydarzenie lub zwróć 404
        event = get_object_or_404(Events, id=event_id, is_active=True)

        # Sprawdź dostępność rezerwacji
        reservation_available = event.is_reservation_available()

        # Jeśli rezerwacja nie jest dostępna, przekieruj do szczegółów wydarzenia
        if not reservation_available:
            messages.warning(request,
                             "Rezerwacja online jest już niedostępna, jeśli chcesz przyjść na koncert to zadzwoń.")
            return redirect('event_detail', event_id=event_id)

        # Przetwarzanie formularza
        form = EventReservationForm(request.POST)

        # Ręcznie ustawiamy pole wydarzenia (które jest ukryte w formularzu)
        form.instance.event = event

        if form.is_valid():
            """Pobierz dane klienta z formularza"""

            customer_data = {
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'email': form.cleaned_data['email'],
                'phone_number': form.cleaned_data['phone_number'],
                'regulations_consent': form.cleaned_data['regulations_consent'],
                'newsletter_consent': form.cleaned_data['newsletter_consent'],
            }

            """Sprawdź czy istnieje już klient o takim e-mailu i numerze telefonu"""

            try:
                customer = Customer.objects.get(
                    email=customer_data['email'],
                    # phone_number=customer_data['phone_number']
                )
                customer.first_name = customer_data['first_name']
                customer.last_name = customer_data['last_name']
                customer.updated_ip = request.client_ip  # Dodaj IP aktualizacji
                customer.save()
            except Customer.DoesNotExist:
                """Utwórz nowego klienta"""
                customer_data['created_ip'] = request.client_ip # Dodaj IP utworzenia
                customer_data['created_by_admin'] = False # Utworzone przez klienta
                customer = Customer.objects.create(**customer_data)

            # Utwórz nowy obiekt rezerwacji bez zapisywania w bazie
            reservation = form.save(commit=False)
            reservation.customer = customer
            reservation.event = event
            reservation.created_ip = request.client_ip # Dodaj IP utworzenia
            reservation.created_by_admin = False # Utworzone przez klienta

            # Sprawdzenie czy liczba uczestników nie przekracza dostępnych miejsc
            participants_count = form.cleaned_data['participants_count']
            available_seats = event.get_available_seats()

            # Ustawiamy status rezerwacji
            if event.is_fully_booked() or participants_count > available_seats:
                # Dodanie do listy rezerwowej
                form.instance.status = Reservations.ReservationStatus.WAITLIST
                form.instance.waitlist_position = event.get_next_waitlist_position()
                message = "Zostałeś dodany do listy rezerwowej. Powiadomimy Cię, jeśli zwolni się miejsce."
            else:
                # Standardowa rezerwacja
                form.instance.status = Reservations.ReservationStatus.CONFIRMED
                message = "Twoja rezerwacja została potwierdzona."

            # Zapisujemy rezerwację
            reservation.save()

            # Wysyłka emaila potwierdzającego
            self.send_email(reservation, 'confirmation')

            # Przekierowanie do strony potwierdzenia zamiast wiadomości flash
            return redirect('reservation_success', event_id=event_id, reservation_id=reservation.id)

        context = {
            'form': form,
            'event': event,
            'reservation_available': reservation_available
        }

        # Dodaj też czas zakończenia rezerwacji w ISO dla JavaScript
        if event.reservation_end_time:
            context['reservation_end_time_iso'] = event.reservation_end_time.isoformat()

        return render(request, 'event_reservation_form.html', context)


class UniversalReservationView(ReservationEmailMixin, View):
    """
    Widok uniwersalnego formularza rezerwacji z możliwością wyboru wydarzenia z listy
    """

    def get(self, request):

        form = UniversalReservationForm()

        # """ Pobierz aktywne wydarzenia do kontekstu (dla JavaScript) """
        # events = Events.objects.filter(
        #     is_active=True,
        #     start_datetime__gte=timezone.now()
        # ).order_by('start_datetime')
        #
        # events_data = {}
        # for event in events:
        #     print(f"Processing event ID: {event.id}, title: {event.title}")
        #     events_data[str(event.id)] = {
        #         'title': event.title,
        #         'start_datetime': event.start_datetime.isoformat(),
        #         'venue_name': event.venue.name,
        #         'venue_address': event.venue.address,
        #         'venue_city': event.venue.city,
        #         'price': str(event.price) if event.price else 'Brak informacji',
        #         'available_seats': event.get_available_seats(),
        #         'is_fully_booked': event.is_fully_booked(),
        #         'reservation_end_time_iso': event.reservation_end_time.isoformat() if event.reservation_end_time else None,
        #         'reservation_available': event.is_reservation_available(),
        #     }
        #     print(f"Added data for event {event.id}")
        # # Po pętli
        # print("Final events_data keys:", list(events_data.keys()))

        context = {
            'form': form,
        }

        return render(request, 'universal_reservation_form.html', context)

    def post(self, request):
        form = UniversalReservationForm(request.POST)

        if form.is_valid():
            event = form.cleaned_data['event']

            """ Sprawdź dostępność rezerwacji dla wybranego wydarzenia """
            if not event.is_reservation_available():
                messages.warning(request, "Rezerwacja online jest już niedostępna dla wybranego wydarzenia.")
                return redirect('universal_reservation')

            """ Pobierz dane klienta z formularza """
            customer_data = {
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'email': form.cleaned_data['email'],
                'phone_number': form.cleaned_data['phone_number'],
                'regulations_consent': form.cleaned_data['regulations_consent'],
                'newsletter_consent': form.cleaned_data['newsletter_consent'],
            }

            """Sprawdź czy istnieje już klient o takim e-mailu i numerze telefonu"""
            """Pierwsze rozwiązanie - występuje błąd"""
            try:
                customer = Customer.objects.get(
                    email=customer_data['email'],
                    # phone_number=customer_data['phone_number']
                )
                customer.first_name = customer_data['first_name']
                customer.last_name = customer_data['last_name']
                customer.updated_ip = request.client_ip  # Dodaj IP aktualizacji
                customer.save()
            except Customer.DoesNotExist:
                """Utwórz nowego klienta"""
                customer_data['created_ip'] = request.client_ip  # Dodaj IP utworzenia
                customer_data['created_by_admin'] = False  # Utworzone przez klienta
                customer = Customer.objects.create(**customer_data)

            """Drugie rozwiązanie - występuje błąd"""
            # defaults = customer_data.copy()
            # email = defaults.pop('email')
            # phone_number = defaults.pop('phone_number')
            #
            # customer, created = Customer.objects.get_or_create(
            #     email=email,
            #     phone_number=phone_number,
            #     defaults=defaults
            # )
            # if not created:
            #     """Jeśli klient istniał, aktualizujemy jego dane"""
            #     customer.first_name = customer_data['first_name']
            #     customer.last_name = customer_data['last_name']
            #     customer.save()

            # Normalizacja danych - usunięcie białych znaków
            # email = customer_data['email'].strip().lower()
            # phone_number = str(customer_data['phone_number'])


            """Rozwiązanie trzecie"""
            # Spróbuj znaleźć klienta z elastycznym zapytaniem
            # try:
            #     # Najpierw sprawdź z dokładnym dopasowaniem
            #     customer = Customer.objects.get(
            #         email=email,
            #         phone_number=phone_number
            # )
            #     # Aktualizuj dane, jeśli klient istnieje
            #     customer.first_name = customer_data['first_name']
            #     customer.last_name = customer_data['last_name']
            #     customer.save(update_fields=['first_name', 'last_name'])
            #
            # except Customer.DoesNotExist:
            #     try:
            #         customer = Customer.objects.create(**customer_data)
            #     except IntegrityError:
            #         """Jeśli nadal występuje problem, szukamy jeszcze raz. Może ktoś inny właśnie utworzył tego klienta"""
            #         customer = Customer.objects.get(
            #             email=email,
            #             phone_number=phone_number
            #         )

            # Utwórz nowy obiekt rezerwacji bez zapisywania w bazie
            reservation = form.save(commit=False)
            reservation.customer = customer
            reservation.event = event
            reservation.created_ip = request.client_ip  # Dodaj IP utworzenia
            reservation.created_by_admin = False  # Utworzone przez klienta

            # Sprawdzenie czy liczba uczestników nie przekracza dostępnych miejsc
            participants_count = form.cleaned_data['participants_count']
            available_seats = event.get_available_seats()

            # Ustawiamy status rezerwacji
            if event.is_fully_booked() or participants_count > available_seats:
                # Dodanie do listy rezerwowej
                form.instance.status = Reservations.ReservationStatus.WAITLIST
                form.instance.waitlist_position = event.get_next_waitlist_position()
                message = "Zostałeś dodany do listy rezerwowej. Powiadomimy Cię, jeśli zwolni się miejsce."
            else:
                # Standardowa rezerwacja
                form.instance.status = Reservations.ReservationStatus.CONFIRMED
                message = "Twoja rezerwacja została potwierdzona."

            # Zapisujemy rezerwację
            reservation.save()

            # Wysyłka emaila potwierdzającego
            self.send_email(reservation, 'confirmation')

            # Przekierowanie do strony potwierdzenia zamiast wiadomości flash
            return redirect('reservation_success', event_id=event.id, reservation_id=reservation.id)
        # Jeśli formularz zawiera błędy, wyświetl go ponownie
        events = Events.objects.filter(
            is_active=True,
            start_datetime__gte=timezone.now()
        ).order_by('start_datetime')

        events_data = {}
        for event in events:
            events_data[event.id] = {
                'title': event.title,
                'start_datetime': event.start_datetime.isoformat(),
                'venue_name': event.venue.name,
                'venue_address': event.venue.address,
                'venue_city': event.venue.city,
                'price': str(event.price) if event.price else "Brak informacji",
                'available_seats': event.get_available_seats(),
                'is_fully_booked': event.is_fully_booked(),
                'reservation_end_time_iso': event.reservation_end_time.isoformat() if event.reservation_end_time else None,
                'reservation_available': event.is_reservation_available(),
            }

        context = {
            'form': form,
            'events_data': json.dumps(events_data),
            'events': events,
        }

        return render(request, 'universal_reservation_form.html', context)

class EventsDataApiView(View):
    """
    API dostarczające dane o aktywnych wydarzeniach w formacie JSON
    """
    def get(self, request):
        """  Pobierz wszystkie aktywne, przyszłe wydarzenia """
        events = Events.objects.filter(
            is_active=True,
            start_datetime__gte=timezone.now()
        ).order_by('start_datetime')

        """ Przygotuj dane w formacie JSON """
        events_data = {}
        for event in events:
            events_data[str(event.id)] = {
                'id': event.id,
                'title': event.title,
                'start_datetime': event.start_datetime.isoformat(),
                'end_datetime': event.end_datetime.isoformat(),
                'venue_name': event.venue.name,
                'venue_address': event.venue.address,
                'venue_city': event.venue.city,
                'price': str(event.price) if event.price else "Brak informacji",
                'available_seats': event.get_available_seats(),
                'is_fully_booked': event.is_fully_booked(),
                'reservation_end_time_iso': event.reservation_end_time.isoformat() if event.reservation_end_time else None,
                'reservation_available': event.is_reservation_available(),
            }
        """ Zwróć dane w formie odpowiedzi JSON """
        return JsonResponse(events_data)


class EventTypeMixin(ContextMixin):
    """
    Mixin dodający typy wydarzeń do kontekstu.
    Przydatny we wszystkich widokach, które potrzebują listy typów do filtrowania.
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event_types'] = EventType.objects.filter(is_active=True)
        return context


class EventListView(EventTypeMixin, ListView):
    """
    Widok wyświetlający listę wszystkich aktywnych, nadchodzących wydarzeń.
    Umożliwia filtrowanie po typie wydarzenia.
    """
    model = Events
    template_name = 'events/event_list.html'
    context_object_name = 'events'

    def get_queryset(self):
        # Pobieramy tylko aktywne wydarzenia z datą rozpoczęcia w przyszłości
        queryset = Events.objects.filter(
            is_active=True,
            start_datetime__gte=timezone.now()
        ).order_by('start_datetime')

        # Opcjonalne filtrowanie po typie wydarzenia
        selected_type = self.request.GET.get('type')
        if selected_type:
            queryset = queryset.filter(type_of_events__slug=selected_type)

        return queryset

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     # Dodajemy informację o wybranym typie do kontekstu
    #     context['selected_type'] = self.request.GET.get('type')
    #     return context


class EventDetailView(EventTypeMixin, DetailView):
    """
    Widok wyświetlający szczegóły pojedynczego wydarzenia.
    Zawiera dodatkowe informacje, takie jak galeria zdjęć.
    """
    model = Events
    template_name = 'event_detail.html'
    context_object_name = 'event'
    pk_url_kwarg = 'event_id'  # Określa nazwę parametru ID w URL

    def get_queryset(self):
        # Ograniczamy do aktywnych wydarzeń
        return Events.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Dodajemy wszystkie zdjęcia wydarzenia do kontekstu
        context['images'] = self.object.images.all().order_by('order')
        context['reservation_available'] = self.object.is_reservation_available()

        # Dodajemy formatowanie czasu dla JavaScript
        if self.object.reservation_end_time:
            context['reservation_end_time_iso'] = self.object.reservation_end_time.isoformat()

        return context


class EventsByTypeView(EventListView):
    """
    Widok wyświetlający wydarzenia określonego typu.
    Dziedziczy po EventListView, co pozwala na reużycie logiki.
    """

    def get_queryset(self):
        # Pobieramy typ wydarzenia lub zwracamy 404
        self.event_type = get_object_or_404(
            EventType,
            slug=self.kwargs['type_slug'],
            is_active=True
        )

        # Filtrujemy wydarzenia po typie
        return Events.objects.filter(
            is_active=True,
            type_of_events=self.event_type,
            start_datetime__gte=timezone.now()
        ).order_by('start_datetime')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Dodajemy informacje o typie wydarzenia do kontekstu
        context['event_type'] = self.event_type
        context['selected_type'] = self.kwargs['type_slug']
        return context


class CancelReservationView(ReservationEmailMixin, View):
    def get(self, request, token):
        """Wyświetla stronę potwierdzenia anulowania rezerwacji"""
        reservation = get_object_or_404(Reservations, cancellation_token=token)

        # Sprawdź czy można anulować rezerwację
        if reservation.status == Reservations.ReservationStatus.CANCELLED:
            messages.warning(request, "Ta rezerwacja została już anulowana.")
            return redirect('index')

        return render(request, 'cancel_reservation.html', {
            'reservation': reservation
        })

    def post(self, request, token):
        """Obsługuje anulowanie rezerwacji"""
        reservation = get_object_or_404(Reservations, cancellation_token=token)

        # Sprawdź czy można anulować rezerwację
        if reservation.status == Reservations.ReservationStatus.CANCELLED:
            messages.warning(request, "Ta rezerwacja została już anulowana.")
            return redirect('index')

        # Zapisz oryginalny status
        # original_status = reservation.status

        # Anuluj rezerwację
        cancel_reservation(reservation)

        # Wysyła e-mail z potwierdzeniem anulowania rezerwacji
        self.send_email(reservation, 'cancellation')

        # Dostosuj komunikat w zależności od oryginalnego statusu
        # if original_status == Reservations.ReservationStatus.WAITLIST:
        #     messages.success(request, "Twoja rezerwacja na liście rezerwowej została pomyślnie anulowana.")
        # else:  # CONFIRMED
        #     messages.success(request, "Twoja rezerwacja została pomyślnie anulowana.")

        # messages.success(request, "Twoja rezerwacja została pomyślnie anulowana.")

        # Jeśli anulowana rezerwacja była potwierdzona, informuj o automatycznym przesunięciu z listy rezerwowej
        # if reservation.status == Reservations.ReservationStatus.CONFIRMED:
        #     if reservation.event.reservations.filter(
        #             status=Reservations.ReservationStatus.CONFIRMED,
        #             waitlist_position__isnull=True
        #     ).exclude(id=reservation.id).exists():
        #         messages.info(request, "Osoba z listy rezerwowej została automatycznie przesunięta na Twoje miejsce.")
        #
        return redirect('index')


class CalendarView(TemplateView):
    """
      Widok strony z kalendarzem wydarzeń.
      Wykorzystuje TemplateView do renderowania strony z kalendarzem.
      """

    template_name = 'event_calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pobierz wszystkie aktywne typy wydarzeń do filtrowania
        context['event_types'] = EventType.objects.filter(is_active=True)
        return context


class CalendarEventsApiView(View):
    """
     API dostarczające wydarzenia w formacie kompatybilnym z FullCalendar.
     Zwraca dane jako JSON.
     """

    def get(self, request, *args, **kwargs):
        # Pobierz filtr typu wydarzenia z query stringa (opcjonalnie)
        event_type = request.GET.get('type')

        # Przygotuj bazowe zapytanie
        events_query = Events.objects.filter(is_active=True)

        # Zastosuj filtrowanie po typie (jeśli podano)
        if event_type:
            events_query = events_query.filter(type_of_events__slug=event_type)

        # Konwertuj wydarzenia do formatu FullCalendar

        events_data = []
        for event in events_query:
            events_data.append({
                'id': event.id,
                'title': event.title,
                'start': event.start_datetime.isoformat(),
                'end': event.end_datetime.isoformat(),
                'url': reverse('event_detail', args=[event.id]),
                # Dodajemy właściwości wizualne
                'backgroundColor': self.get_event_color(event.type_of_events),
                'borderColor': self.get_event_color(event.type_of_events),
                # Dodajemy informacje o dostępności
                'extendedProps': {
                    'venue': str(event.venue),
                    'available_seats': event.get_available_seats(),
                    'is_fully_booked': event.is_fully_booked(),
                    'event_type': event.type_of_events.name
                }
            })

        return JsonResponse(events_data, safe=False)

    def get_event_color(self, event_type):
        """
        Zwraca kolor na podstawie typu wydarzenia.
        Jeśli model EventType ma pole color, używa go, w przeciwnym razie
        stosuje domyślne kolory na podstawie sluga.
        """
        # Sprawdź czy model ma pole color
        if hasattr(event_type, 'color') and event_type.color:
            return event_type.color

        # Domyślne kolory na podstawie sluga
        colors = {
            'concert': '#3788d8',  # niebieski
            'workshop': '#f07c4a',  # pomarańczowy
            'meeting': '#8cbd46',  # zielony
            'other': '#9d7cd8'  # fioletowy
        }
        return colors.get(event_type.slug, '#3788d8')  # domyślny niebieski


class ReservationAvailabilityView(View):
    """
    API endpoint do sprawdzania dostępności rezerwacji.
    Zwraca JSON z informacją, czy rezerwacja jest dostępna.
    """

    def get(self, request, event_id):
        event = get_object_or_404(Events, id=event_id, is_active=True)
        is_available = event.is_reservation_available()

        return JsonResponse({
            'available': is_available,
            'current_time': timezone.now().isoformat(),
            'end_time': event.reservation_end_time.isoformat() if event.reservation_end_time else None,
            'message': "Rezerwacja online jest już niedostępna, jeśli chcesz przyjść na koncert to zadzwoń pod numer: "
                       "509 55 33 66." if not is_available else ""
        })
