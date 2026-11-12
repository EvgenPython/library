from django.db import migrations, models
import django.db.models.deletion
import library.models

class Migration(migrations.Migration):
    dependencies = [('library', '0001_initial')]
    operations = [
        migrations.CreateModel(name='StudentWorkArchive', fields=[
            ('id', models.BigAutoField(primary_key=True, serialize=False)),
            ('title', models.CharField(max_length=350, verbose_name='Назва архіву')),
            ('work_type', models.CharField(choices=[('course', 'Курсова робота'), ('diploma', 'Дипломна робота')], default='course', max_length=10, verbose_name='Тип роботи')),
            ('group', models.CharField(db_index=True, max_length=80, verbose_name='Група')),
            ('year', models.PositiveSmallIntegerField(db_index=True, verbose_name='Рік')),
            ('description', models.TextField(blank=True, verbose_name='Опис')),
            ('file', models.FileField(storage=library.models.private_storage, upload_to=library.models.work_archive_path, validators=[library.models.validate_work_archive], verbose_name='ZIP-архів')),
            ('is_published', models.BooleanField(default=True, verbose_name='Опубліковано')),
            ('added_at', models.DateTimeField(auto_now_add=True, verbose_name='Додано')),
            ('subject', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='work_archives', to='library.subject', verbose_name='Дисципліна')),
        ], options={'verbose_name':'Архів студентських робіт','verbose_name_plural':'Репозиторій робіт','ordering':['-year','-added_at']}),
    ]
