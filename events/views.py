from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.views import View
from events.forms import RezerwationForm
from django.contrib import messages


# Create your views here.

class HomeView(View):
    def get(self, request):
        return render(request, 'index.html')


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
