from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import library.models

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name='Institution', fields=[
            ('id', models.BigAutoField(primary_key=True, serialize=False)),
            ('name', models.CharField(max_length=255, verbose_name='Назва закладу')),
            ('slug', models.SlugField(unique=True, verbose_name='Код закладу')),
            ('description', models.TextField(blank=True, verbose_name='Опис')),
            ('is_active', models.BooleanField(default=True, verbose_name='Активний')),
        ], options={'verbose_name':'Заклад освіти','verbose_name_plural':'Заклади освіти','ordering':['name']}),
        migrations.CreateModel(name='Subject', fields=[
            ('id', models.BigAutoField(primary_key=True, serialize=False)),
            ('title', models.CharField(max_length=255, verbose_name='Дисципліна')),
            ('description', models.TextField(blank=True, verbose_name='Опис')),
            ('is_active', models.BooleanField(default=True, verbose_name='Відображати студентам')),
            ('sort_order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
            ('institution', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='subjects', to='library.institution', verbose_name='Заклад')),
        ], options={'verbose_name':'Дисципліна','verbose_name_plural':'Дисципліни','ordering':['sort_order','title']}),
        migrations.CreateModel(name='Book', fields=[
            ('id', models.BigAutoField(primary_key=True, serialize=False)),
            ('title', models.CharField(max_length=350, verbose_name='Назва книги')),
            ('author', models.CharField(blank=True, max_length=255, verbose_name='Автор')),
            ('description', models.TextField(blank=True, verbose_name='Опис')),
            ('file', models.FileField(storage=library.models.private_storage, upload_to=library.models.book_path, validators=[library.models.validate_book_file], verbose_name='Файл книги')),
            ('is_published', models.BooleanField(default=True, verbose_name='Опубліковано')),
            ('added_at', models.DateTimeField(auto_now_add=True, verbose_name='Додано')),
            ('subject', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='books', to='library.subject', verbose_name='Дисципліна')),
        ], options={'verbose_name':'Книга','verbose_name_plural':'Книги','ordering':['title']}),
        migrations.CreateModel(name='StudentProfile', fields=[
            ('id', models.BigAutoField(primary_key=True, serialize=False)),
            ('must_change_password', models.BooleanField(default=True, verbose_name='Змінити тимчасовий пароль')),
            ('active_institution', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='library.institution', verbose_name='Обраний заклад')),
            ('institutions', models.ManyToManyField(blank=True, related_name='students', to='library.institution', verbose_name='Дозволені заклади')),
            ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='student_profile', to=settings.AUTH_USER_MODEL)),
        ], options={'verbose_name':'Профіль студента','verbose_name_plural':'Профілі студентів'}),
        migrations.AddConstraint(model_name='subject', constraint=models.UniqueConstraint(fields=('institution','title'), name='unique_institution_subject')),
    ]
