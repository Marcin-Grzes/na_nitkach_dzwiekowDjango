from django.shortcuts import render, redirect
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
            type_of_payments = form.cleaned_data['type_of_payments']
            form.save()
            messages.success(request, "Rezerwacja została przyjęta pomyślnie!")
            return redirect('home')
        return render(request, 'rezerwation_form.html', {"form": form})
