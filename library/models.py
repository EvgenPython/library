from pathlib import Path
from uuid import uuid4
from datetime import date
import zipfile

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.db import models

private_storage = FileSystemStorage(location=settings.PRIVATE_MEDIA_ROOT)

def validate_book_file(file):
    if Path(file.name).suffix.lower() not in {'.pdf', '.epub', '.doc', '.docx', '.txt', '.rtf', '.djvu'}:
        raise ValidationError('Допустимі PDF, EPUB, DOC, DOCX, TXT, RTF, DJVU.')
    if file.size > 50 * 1024 * 1024:
        raise ValidationError('Максимум 50 МБ.')

def book_path(instance, filename):
    return f'books/{uuid4().hex}{Path(filename).suffix.lower()}'

def validate_work_archive(file):
    if Path(file.name).suffix.lower() != '.zip':
        raise ValidationError('Дозволені лише ZIP-архіви.')
    if file.size > 200 * 1024 * 1024:
        raise ValidationError('Максимум 200 МБ.')
    try:
        file.seek(0)
        with zipfile.ZipFile(file) as archive:
            entries = archive.infolist()
            if len(entries) > 10000 or sum(item.file_size for item in entries) > 2 * 1024**3:
                raise ValidationError('Архів перевищує ліміт кількості чи розміру файлів.')
            if any(item.flag_bits & 1 for item in entries):
                raise ValidationError('Захищені паролем архіви не підтримуються.')
    except (zipfile.BadZipFile, OSError, ValueError):
        raise ValidationError('Некоректний ZIP-архів.')
    finally:
        file.seek(0)

def work_archive_path(instance, filename):
    return f'works/{uuid4().hex}.zip'

class Institution(models.Model):
    name = models.CharField('Назва закладу', max_length=255)
    slug = models.SlugField('Код закладу', unique=True)
    description = models.TextField('Опис', blank=True)
    is_active = models.BooleanField('Активний', default=True)
    class Meta:
        verbose_name = 'Заклад освіти'
        verbose_name_plural = 'Заклади освіти'
        ordering = ['name']
    def __str__(self):
        return self.name

class Subject(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.PROTECT, related_name='subjects', verbose_name='Заклад')
    title = models.CharField('Дисципліна', max_length=255)
    description = models.TextField('Опис', blank=True)
    is_active = models.BooleanField('Відображати студентам', default=True)
    sort_order = models.PositiveIntegerField('Порядок', default=0)
    class Meta:
        verbose_name = 'Дисципліна'
        verbose_name_plural = 'Дисципліни'
        ordering = ['sort_order', 'title']
        constraints = [models.UniqueConstraint(fields=['institution', 'title'], name='unique_institution_subject')]
    def __str__(self):
        return f'{self.title} · {self.institution}'

class Book(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name='books', verbose_name='Дисципліна')
    title = models.CharField('Назва книги', max_length=350)
    author = models.CharField('Автор', max_length=255, blank=True)
    description = models.TextField('Опис', blank=True)
    file = models.FileField('Файл книги', storage=private_storage, upload_to=book_path, validators=[validate_book_file])
    is_published = models.BooleanField('Опубліковано', default=True)
    added_at = models.DateTimeField('Додано', auto_now_add=True)
    class Meta:
        verbose_name = 'Книга'
        verbose_name_plural = 'Книги'
        ordering = ['title']
    def __str__(self):
        return self.title
    @property
    def file_extension(self):
        return Path(self.file.name).suffix[1:].upper()

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    institutions = models.ManyToManyField(Institution, blank=True, related_name='students', verbose_name='Дозволені заклади')
    active_institution = models.ForeignKey(Institution, on_delete=models.SET_NULL, null=True, blank=True, related_name='+', verbose_name='Обраний заклад')
    must_change_password = models.BooleanField('Змінити тимчасовий пароль', default=True)
    class Meta:
        verbose_name = 'Профіль студента'
        verbose_name_plural = 'Профілі студентів'
    def __str__(self):
        return self.user.get_full_name() or self.user.username

class StudentWorkArchive(models.Model):
    TYPES = [('course', 'Курсова робота'), ('diploma', 'Дипломна робота')]
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name='work_archives', verbose_name='Дисципліна')
    title = models.CharField('Назва архіву', max_length=350)
    work_type = models.CharField('Тип роботи', max_length=10, choices=TYPES, default='course')
    group = models.CharField('Група', max_length=80, db_index=True)
    year = models.PositiveSmallIntegerField('Рік', db_index=True)
    description = models.TextField('Опис', blank=True)
    file = models.FileField('ZIP-архів', storage=private_storage, upload_to=work_archive_path, validators=[validate_work_archive])
    is_published = models.BooleanField('Опубліковано', default=True)
    added_at = models.DateTimeField('Додано', auto_now_add=True)
    class Meta:
        verbose_name = 'Архів студентських робіт'
        verbose_name_plural = 'Репозиторій робіт'
        ordering = ['-year', '-added_at']
    def __str__(self):
        return f'{self.title} — {self.group} ({self.year})'
    def clean(self):
        if self.year and not 2000 <= self.year <= date.today().year + 1:
            raise ValidationError({'year': 'Некоректний рік.'})
