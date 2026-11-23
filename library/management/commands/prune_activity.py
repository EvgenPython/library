from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from library.models import StudentActivity


class Command(BaseCommand):
    help = 'Видалити журнали студентської активності старші за вказаний період.'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=365, help='Період зберігання у днях (типово 365).')
        parser.add_argument('--dry-run', action='store_true', help='Показати кількість без видалення.')

    def handle(self, *args, **options):
        if options['days'] < 1:
            raise CommandError('--days має бути не менше 1')
        cutoff = timezone.now() - timedelta(days=options['days'])
        qs = StudentActivity.objects.filter(created_at__lt=cutoff)
        count = qs.count()
        if not options['dry_run']:
            qs.delete()
        self.stdout.write(f'{"Знайдено" if options["dry_run"] else "Видалено"} записів: {count}')
