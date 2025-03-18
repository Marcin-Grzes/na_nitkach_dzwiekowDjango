from django.utils import timezone
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.views import View
from django.views.generic import ListView, DetailView
from django.views.generic.base import ContextMixin

from events.forms import RezerwationForm, EventReservationForm
from django.contrib import messages

from events.models import EventType, Events, Rezerwations
from events.services import cancel_reservation


# Create your views here.

class HomeView(View):
    def get(self, request):
        return render(request, 'index.html')


class EventReservationView(View):
    """
    Widok do rezerwacji miejsc na konkretne wydarzenie.
    Przyjmuje ID wydarzenia z URL i tworzy odpowiednią rezerwację.
    """

    def get(self, request, event_id):
        # Pobierz wydarzenie lub zwróć 404
        event = get_object_or_404(Events, id=event_id, is_active=True)

        # Sprawdź czy są jeszcze miejsca
        if event.is_fully_booked():
            messages.warning(
                request,
                "Wszystkie miejsca na to wydarzenie są już zajęte. Możesz zapisać się na listę rezerwową."
            )

        # Tworzenie formularza pre-konfigurowanego dla tego wydarzenia
        form = EventReservationForm(initial={'event': event})

        context = {
            'form': form,
            'event': event,
        }
        return render(request, 'events/event_reservation.html', context)

    def post(self, request, event_id):
        # Pobierz wydarzenie lub zwróć 404
        event = get_object_or_404(Events, id=event_id, is_active=True)

        # Przetwarzanie formularza
        form = EventReservationForm(request.POST)

        # Ręcznie ustawiamy pole wydarzenia (które jest ukryte w formularzu)
        form.instance.event = event

        if form.is_valid():
            # Sprawdzenie czy liczba uczestników nie przekracza dostępnych miejsc
            participants_count = form.cleaned_data['participants_count']
            available_seats = event.get_available_seats()

            # Ustawiamy status rezerwacji
            if event.is_fully_booked() or participants_count > available_seats:
                # Dodanie do listy rezerwowej
                form.instance.status = Rezerwations.ReservationStatus.WAITLIST
                form.instance.waitlist_position = event.get_next_waitlist_position()
                message = "Zostałeś dodany do listy rezerwowej. Powiadomimy Cię, jeśli zwolni się miejsce."
            else:
                # Standardowa rezerwacja
                form.instance.status = Rezerwations.ReservationStatus.CONFIRMED
                message = "Twoja rezerwacja została potwierdzona."

            # Zapisujemy rezerwację
            reservation = form.save()

            # Wysyłka emaila potwierdzającego
            self.send_confirmation_email(reservation)

            messages.success(request, message)
            return redirect('event_detail', event_id=event_id)

        context = {'form': form, 'event': event}
        return render(request, 'events/event_reservation.html', context)

    def send_confirmation_email(self, reservation):
        subject = f'Potwierdzenie rezerwacji - {reservation.event.title}'

        # Kontekst do szablonu z danymi wydarzenia
        context = {
            'first_name': reservation.first_name,
            'last_name': reservation.last_name,
            'participants_count': reservation.participants_count,
            'email': reservation.email,
            'phone_number': str(reservation.phone_number),
            'payment_method': reservation.get_type_of_payments_display(),
            'event': reservation.event,  # Dodanie informacji o wydarzeniu
        }

        # Generowanie wiadomości HTML z szablonu
        html_message = render_to_string('event_reservation_confirmation.html', context)
        plain_message = strip_tags(html_message)

        # Wysyłanie emaila
        send_mail(
            subject,
            plain_message,
            None,  # używa DEFAULT_FROM_EMAIL z ustawień
            [reservation.email],
            html_message=html_message,
        )



class RezerwationsView(View):

    def get(self, request):
        form = RezerwationForm()
        return render(request, 'rezerwation_form.html', {"form": form})

    def post(self, request):
        form = RezerwationForm(request.POST)
        if form.is_valid():
            imie = form.cleaned_data['first_name']
            nazwisko = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            numer_telefonu = form.cleaned_data['phone_number']
            sposob_platnosci = form.cleaned_data['type_of_payments']
            liczba_uczestnikow = form.cleaned_data['participants_count']
            reservation = form.save()
            # Wysyłka emaila potwierdzającego
            self.send_confirmation_email(reservation)
            messages.success(request, "Rezerwacja została przyjęta pomyślnie!")
            return redirect('home')
        return render(request, 'rezerwation_form.html', {"form": form})

    def send_confirmation_email(self, reservation):
        subject = 'Potwierdzenie rezerwacji'

        # Kontekst do szablonu
        context = {
            'first_name': reservation.first_name,
            'last_name': reservation.last_name,
            'participants_count': reservation.participants_count,
            'email': reservation.email,
            'phone_number': str(reservation.phone_number),
            'payment_method': reservation.get_type_of_payments_display(),  # używa metody display dla choices
        }

        # Generowanie wiadomości HTML z szablonu
        html_message = render_to_string('mail_reservation_confirmation.html', context)
        plain_message = strip_tags(html_message)  # wersja tekstowa

        # Wysyłanie emaila
        send_mail(
            subject,
            plain_message,
            None,  # używa DEFAULT_FROM_EMAIL z ustawień
            [reservation.email],
            html_message=html_message,
        )


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Dodajemy informację o wybranym typie do kontekstu
        context['selected_type'] = self.request.GET.get('type')
        return context


class EventDetailView(EventTypeMixin, DetailView):
    """
    Widok wyświetlający szczegóły pojedynczego wydarzenia.
    Zawiera dodatkowe informacje, takie jak galeria zdjęć.
    """
    model = Events
    template_name = 'events/event_detail.html'
    context_object_name = 'event'
    pk_url_kwarg = 'event_id'  # Określa nazwę parametru ID w URL

    def get_queryset(self):
        # Ograniczamy do aktywnych wydarzeń
        return Events.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Dodajemy wszystkie zdjęcia wydarzenia do kontekstu
        context['images'] = self.object.images.all().order_by('order')
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


class CancelReservationView(View):
    def get(self, request, token):
        """Wyświetla stronę potwierdzenia anulowania rezerwacji"""
        reservation = get_object_or_404(Rezerwations, cancellation_token=token)

        # Sprawdź czy można anulować rezerwację
        if reservation.status == Rezerwations.ReservationStatus.CANCELLED:
            messages.warning(request, "Ta rezerwacja została już anulowana.")
            return redirect('home')

        return render(request, 'events/cancel_reservation_confirm.html', {
            'reservation': reservation
        })

    def post(self, request, token):
        """Obsługuje anulowanie rezerwacji"""
        reservation = get_object_or_404(Rezerwations, cancellation_token=token)

        # Sprawdź czy można anulować rezerwację
        if reservation.status == Rezerwations.ReservationStatus.CANCELLED:
            messages.warning(request, "Ta rezerwacja została już anulowana.")
            return redirect('home')

        # Anuluj rezerwację
        cancel_reservation(reservation)

        messages.success(request, "Twoja rezerwacja została pomyślnie anulowana.")

        # Jeśli anulowana rezerwacja była potwierdzona, informuj o automatycznym przesunięciu z listy rezerwowej
        if reservation.status == Rezerwations.ReservationStatus.CONFIRMED:
            if reservation.event.reservations.filter(
                    status=Rezerwations.ReservationStatus.CONFIRMED,
                    waitlist_position__isnull=True
            ).exclude(id=reservation.id).exists():
                messages.info(request, "Osoba z listy rezerwowej została automatycznie przesunięta na Twoje miejsce.")

        return redirect('home')