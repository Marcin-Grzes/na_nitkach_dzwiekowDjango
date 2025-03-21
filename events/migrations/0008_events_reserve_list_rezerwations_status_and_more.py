# Generated by Django 5.2b1 on 2025-03-18 07:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0007_alter_events_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='events',
            name='reserve_list',
            field=models.PositiveIntegerField(default=0, verbose_name='Lista rezerwowa'),
        ),
        migrations.AddField(
            model_name='rezerwations',
            name='status',
            field=models.CharField(choices=[('confirmed', 'Potwierdzona'), ('waitlist', 'Lista rezerwowa'), ('cancelled', 'Anulowana')], default='confirmed', max_length=20, verbose_name='Status rezerwacji'),
        ),
        migrations.AddField(
            model_name='rezerwations',
            name='waitlist_position',
            field=models.PositiveIntegerField(blank=True, help_text="Pozycja na liście rezerwowej (tylko dla rezerwacji w statusie 'Lista rezerwowa')", null=True, verbose_name='Pozycja na liście rezerwowej'),
        ),
    ]
