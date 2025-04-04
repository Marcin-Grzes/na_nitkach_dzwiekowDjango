# Generated by Django 5.2b1 on 2025-03-14 19:03

import phonenumber_field.modelfields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Rezerwations',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=50, verbose_name='Imię')),
                ('last_name', models.CharField(max_length=50, verbose_name='Nazwisko')),
                ('email', models.EmailField(max_length=254, verbose_name='Adres email')),
                ('phone_number', phonenumber_field.modelfields.PhoneNumberField(max_length=128, region='PL', verbose_name='Numer telefonu')),
                ('type_of_payments', models.CharField(choices=[('cash', 'Gotówka na miejscu'), ('blik', 'BLIK')], default='cash', max_length=10, verbose_name='Typ płatności')),
                ('data_processing_consent', models.BooleanField(default=False, help_text='Wyrażam zgodę na przetwarzanie moich danych osobowych niezbędnych do realizacji spotkania.', verbose_name='Zgoda na przetwarzanie danych')),
                ('privacy_policy_consent', models.BooleanField(default=False, help_text='Oświadczam, że zapoznałem się z polityką prywatności i akceptuję jej warunki.', verbose_name='Zgoda na politykę prywatności')),
                ('marketing_emails_consent', models.BooleanField(default=False, help_text='Wyrażam zgodę na otrzymywanie informacji o przyszłych wydarzeniach i ofertach specjalnych.', verbose_name='Zgoda marketingowa')),
                ('reminder_emails_consent', models.BooleanField(default=False, help_text='Wyrażam zgodę na otrzymywanie przypomnienia o zbliżającym się koncercie', verbose_name='Zgoda na przypomnienie o spotkaniu')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Data utworzenia')),
            ],
            options={
                'verbose_name': 'Rezerwacja',
                'verbose_name_plural': 'Rezerwacje',
            },
        ),
    ]
