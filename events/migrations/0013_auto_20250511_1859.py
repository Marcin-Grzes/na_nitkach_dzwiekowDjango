# Generated by Django 5.1.7 on 2025-05-11 16:59

from django.db import migrations

def migrate_customer_data(apps, schema_editor):
    """Pobierz modele z stanu aplikacji w momencie migracji"""
    Rezerwations = apps.get_model('events', 'Rezerwations')
    Customer = apps.get_model('accounts', 'Customer')  # Właściwa aplikacja

    """ Grupuj rezerwacje po danych klienta aby uniknąć duplikatów """
    customer_data = {}

    for reservation in Rezerwations.objects.all():
        """ Tworzenie klucza unikalności dla klienta """
        customer_key = (reservation.email, str(reservation.phone_number))

        if customer_key not in customer_data:
            # Zapisz dane pierwszej rezerwacji dla tego klienta
            customer_data[customer_key] = {
                'first_name': reservation.first_name,
                'last_name': reservation.last_name,
                'email': reservation.email,
                'phone_number': reservation.phone_number,
                'regulations_consent': reservation.regulations_consent,
                'newsletter_consent': reservation.newsletter_consent,
                'created_at': reservation.created_at,
                'reservations': []
            }

            # Dodaj tę rezerwację do listy rezerwacji klienta
        customer_data[customer_key]['reservations'].append(reservation)

        # Teraz utwórz klientów i aktualizuj rezerwacje
        for customer_info in customer_data.values():
            reservations = customer_info.pop('reservations')

            # Utwórz nowego klienta
            customer = Customer.objects.create(**customer_info)

            # Zaktualizuj rezerwacje
            for reservation in reservations:
                reservation.customer = customer
                reservation.save()


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0012_remove_rezerwations_data_processing_consent_and_more'),
        ('accounts', '0001_initial'),  # Zależność od migracji accounts
    ]

    operations = [
        migrations.RunPython(migrate_customer_data, migrations.RunPython.noop),
    ]

