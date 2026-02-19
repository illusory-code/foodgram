import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from recipes.models import Ingredient, Tag


class Command(BaseCommand):
    """Команда импорта данных из CSV-файлов."""

    help = 'Загружает ингредиенты и теги из CSV в базу данных'

    def add_arguments(self, parser):
        parser.add_argument(
            '--ingredients',
            type=str,
            default='data/ingredients.csv',
            help='Путь к CSV-файлу с ингредиентами',
        )
        parser.add_argument(
            '--tags',
            type=str,
            default='data/tags.csv',
            help='Путь к CSV-файлу с тегами',
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Пропустить существующие записи',
        )

    def _parse_csv(self, filepath):
        """Чтение и парсинг CSV-файла."""
        path = Path(filepath)
        if not path.exists():
            raise CommandError(f'Файл не найден: {filepath}')

        with open(path, encoding='utf-8', newline='') as file:
            return list(csv.reader(file))

    def _load_ingredients(self, filepath, skip_existing):
        """Загрузка ингредиентов в БД."""
        rows = self._parse_csv(filepath)
        if not rows:
            self.stdout.write(self.style.WARNING('Файл ингредиентов пуст'))
            return

        created = 0
        skipped = 0

        start_row = 0
        if rows and rows[0] and rows[0][0] == 'name':
            start_row = 1
            self.stdout.write('Пропускаем строку заголовков')
        for row in rows[start_row:]:
            if len(row) < 3:
                continue

            name, unit = row[0].strip(), row[1].strip()

            if skip_existing and Ingredient.objects.filter(
                name=name,
                measurement_unit=unit
            ).exists():
                skipped += 1
                continue

            Ingredient.objects.get_or_create(
                name=name,
                defaults={'measurement_unit': unit}
            )
            created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Ингредиенты: создано {created}, пропущено {skipped}'
            )
        )

    def _load_tags(self, filepath, skip_existing):
        """Загрузка тегов в БД."""
        rows = self._parse_csv(filepath)
        if not rows:
            self.stdout.write(self.style.WARNING('Файл тегов пуст'))
            return

        created = 0
        skipped = 0

        for row in rows:
            if len(row) < 3:
                continue

            name, color, slug = row[0].strip(), row[1].strip(), row[2].strip()

            if skip_existing and Tag.objects.filter(slug=slug).exists():
                skipped += 1
                continue

            Tag.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'color_code': color,
                }
            )
            created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Теги: создано {created}, пропущено {skipped}'
            )
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Начинаем импорт данных...'))

        try:
            self._load_ingredients(
                options['ingredients'],
                options['skip_existing']
            )
            self._load_tags(
                options['tags'],
                options['skip_existing']
            )
            self.stdout.write(self.style.SUCCESS('Импорт завершён!'))
        except Exception as error:
            raise CommandError(f'Ошибка импорта: {error}')
