import csv
import os
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from recipes.models import Ingredient, Tag


class LoadDataCommand(BaseCommand):
    """Команда для импорта данных из CSV-файлов."""

    help = 'Импортирует ингредиенты и теги из CSV в БД'

    def add_arguments(self, parser):
        parser.add_argument(
            '--ingredients-file',
            type=str,
            default='data/ingredients.csv',
            help='Путь к файлу с ингредиентами',
        )
        parser.add_argument(
            '--tags-file',
            type=str,
            default='data/tags.csv',
            help='Путь к файлу с тегами',
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Пропустить существующие записи',
        )

    def _read_csv_file(self, filepath):
        """Чтение CSV-файла с валидацией."""
        path = Path(filepath)
        if not path.exists():
            raise CommandError(f'Файл не найден: {filepath}')
        
        with open(path, encoding='utf-8', newline='') as f:
            return list(csv.reader(f))

    def _import_ingredients(self, filepath, skip_existing):
        """Импорт ингредиентов."""
        rows = self._read_csv_file(filepath)
        if not rows:
            self.stdout.write(self.style.WARNING('Файл ингредиентов пуст'))
            return

        created_count = 0
        skipped_count = 0

        for row in rows:
            if len(row) < 2:
                continue
            
            name, unit = row[0].strip(), row[1].strip()
            
            if skip_existing and Ingredient.objects.filter(name=name, unit=unit).exists():
                skipped_count += 1
                continue

            Ingredient.objects.get_or_create(
                name=name,
                defaults={'unit': unit}
            )
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Ингредиенты: создано {created_count}, пропущено {skipped_count}'
            )
        )

    def _import_tags(self, filepath, skip_existing):
        """Импорт тегов."""
        rows = self._read_csv_file(filepath)
        if not rows:
            self.stdout.write(self.style.WARNING('Файл тегов пуст'))
            return

        created_count = 0
        skipped_count = 0

        for row in rows:
            if len(row) < 3:
                continue
            
            name, color, slug = row[0].strip(), row[1].strip(), row[2].strip()
            
            if skip_existing and Tag.objects.filter(slug=slug).exists():
                skipped_count += 1
                continue

            Tag.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'color_code': color,
                }
            )
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Теги: создано {created_count}, пропущено {skipped_count}'
            )
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Начинаем импорт данных...'))
        
        try:
            self._import_ingredients(
                options['ingredients_file'],
                options['skip_existing']
            )
            self._import_tags(
                options['tags_file'],
                options['skip_existing']
            )
            self.stdout.write(self.style.SUCCESS('Импорт завершён успешно!'))
        except Exception as exc:
            raise CommandError(f'Ошибка импорта: {exc}')
