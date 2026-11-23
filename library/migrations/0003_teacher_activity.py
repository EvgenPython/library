from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('library', '0002_studentworkarchive'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='uploaded_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='uploaded_books', to=settings.AUTH_USER_MODEL, verbose_name='Хто додав'),
        ),
        migrations.CreateModel(
            name='TeacherProfile',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,
                    related_name='teacher_profile', to=settings.AUTH_USER_MODEL, verbose_name='Користувач')),
                ('subjects', models.ManyToManyField(blank=True, related_name='teachers',
                    to='library.subject', verbose_name='Закріплені дисципліни')),
            ],
            options={'verbose_name': 'Профіль викладача', 'verbose_name_plural': 'Профілі викладачів'},
        ),
        migrations.CreateModel(
            name='StudentActivity',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('action', models.CharField(choices=[
                    ('login', 'Вхід до кабінету'),
                    ('catalog', 'Каталог'),
                    ('subject', 'Перегляд дисципліни'),
                    ('repository', 'Репозиторій'),
                    ('book_download', 'Запит на завантаження книги'),
                    ('archive_download', 'Запит на завантаження архіву'),
                ], db_index=True, max_length=30, verbose_name='Дія')),
                ('item_title', models.CharField(blank=True, max_length=350, verbose_name='Що переглядав')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Дата й час')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                    related_name='library_activity', to=settings.AUTH_USER_MODEL, verbose_name='Студент')),
            ],
            options={'verbose_name': 'Дія студента', 'verbose_name_plural': 'Активність студентів',
                     'ordering': ['-created_at']},
        ),
        migrations.AddIndex(
            model_name='studentactivity',
            index=models.Index(fields=['user', '-created_at'], name='student_activity_user_ts'),
        ),
        migrations.CreateModel(
            name='BookAudit',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('actor_name', models.CharField(max_length=150, verbose_name='Логін на момент дії')),
                ('action', models.CharField(choices=[
                    ('added', 'Додано'), ('edited', 'Змінено'), ('deleted', 'Видалено'),
                ], max_length=12, verbose_name='Дія')),
                ('book_id', models.PositiveBigIntegerField(verbose_name='ID книги')),
                ('book_title', models.CharField(max_length=350, verbose_name='Назва книги')),
                ('subject_title', models.CharField(max_length=255, verbose_name='Дисципліна')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Дата й час')),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='book_audits', to=settings.AUTH_USER_MODEL, verbose_name='Користувач')),
            ],
            options={'verbose_name': 'Історія змін літератури',
                     'verbose_name_plural': 'Історія змін літератури', 'ordering': ['-created_at']},
        ),
    ]
