from django.core.management.base import BaseCommand
from django.utils import timezone
from events.models import Events
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Dezaktywuje wydarzenia, których czas rozpoczęcia już minął'

    def add_arguments(self, parser):
        # Opcjonalny argument --quiet, aby wyciszyć standardowe komunikaty
        parser.add_argument(
            '--quiet',
            action='store_true',
            help='Nie wyświetlaj komunikatów o sukcesie',
        )

    def handle(self, *args, **options):
        try:
            # Znajdź wszystkie aktywne wydarzenia z czasem rozpoczęcia w przeszłości
            now = timezone.now()
            past_events = Events.objects.filter(
                is_active=True,
                start_datetime__lt=now
            )

            # Przechowaj identyfikatory przed aktualizacją (dla logowania)
            event_ids = list(past_events.values_list('id', 'title'))

            # Zaktualizuj statusy na nieaktywne
            count = past_events.update(is_active=False)

            # Logowanie i wyświetlanie informacji
            if count > 0:
                self.log_deactivation(count, event_ids, options.get('quiet', False))
            elif not options.get('quiet', False):
                self.stdout.write(self.style.SUCCESS('Brak wydarzeń do dezaktywacji.'))

            return count

        except Exception as e:
            error_msg = f'Błąd podczas dezaktywacji wydarzeń: {str(e)}'
            logger.error(error_msg)
            self.stderr.write(self.style.ERROR(error_msg))
            raise

    def log_deactivation(self, count, event_ids, quiet=False):
        """Loguje informacje o dezaktywowanych wydarzeniach"""
        events_info = ', '.join([f"ID:{eid} '{title}'" for eid, title in event_ids])
        log_message = f'Dezaktywowano {count} minionych wydarzeń: {events_info}'

        # Logowanie do systemu logów
        logger.info(log_message)

        # Wyświetlenie komunikatu w konsoli (jeśli nie wyciszone)
        if not quiet:
            self.stdout.write(self.style.SUCCESS(f'Pomyślnie dezaktywowano {count} minionych wydarzeń.'))