# Generated by Django 5.2b1 on 2025-03-18 15:00

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0008_events_reserve_list_rezerwations_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='rezerwations',
            name='cancellation_token',
            field=models.UUIDField(default=uuid.uuid4, editable=False, null=True, verbose_name='Token anulowania'),
        ),
    ]
