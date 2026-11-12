import csv
import io
import secrets
import string
from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import path
from .models import Institution, Subject, Book, StudentProfile, StudentWorkArchive

@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active')
    search_fields = ('name', 'slug')
    list_editable = ('is_active',)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'institution', 'is_active', 'sort_order')
    list_filter = ('institution', 'is_active')
    search_fields = ('title', 'institution__name')
    autocomplete_fields = ('institution',)
    list_editable = ('is_active', 'sort_order')

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'subject', 'is_published', 'added_at')
    list_filter = ('subject__institution', 'is_published')
    search_fields = ('title', 'author', 'subject__title')
    autocomplete_fields = ('subject',)
    list_editable = ('is_published',)

@admin.register(StudentWorkArchive)
class StudentWorkArchiveAdmin(admin.ModelAdmin):
    list_display = ('title', 'work_type', 'subject', 'group', 'year', 'is_published')
    list_filter = ('work_type', 'year', 'group', 'subject__institution', 'is_published')
    search_fields = ('title', 'group', 'subject__title', 'description')
    autocomplete_fields = ('subject',)
    list_editable = ('is_published',)

class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    extra = 1
    max_num = 1
    can_delete = False
    filter_horizontal = ('institutions',)

class ImportForm(forms.Form):
    csv_file = forms.FileField(label='CSV-файл студентів')

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'active_institution')
    list_filter = ('institutions',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    autocomplete_fields = ('user', 'active_institution')
    filter_horizontal = ('institutions',)
    change_list_template = 'admin/library/studentprofile/change_list.html'

    def get_urls(self):
        return [path('import-csv/', self.admin_site.admin_view(self.import_csv),
                     name='library_student_import')] + super().get_urls()

    def import_csv(self, request):
        if not request.user.is_superuser:
            raise PermissionDenied
        form = ImportForm(request.POST or None, request.FILES or None)
        if request.method == 'POST' and form.is_valid():
            try:
                raw = form.cleaned_data['csv_file'].read().decode('utf-8-sig')
                reader = csv.DictReader(io.StringIO(raw))
                required = {'username', 'first_name', 'last_name', 'institution_slug'}
                if not required.issubset(reader.fieldnames or []):
                    raise ValueError('Потрібні колонки: username,first_name,last_name,institution_slug')
                rows = list(reader)
                if not 1 <= len(rows) <= 1000:
                    raise ValueError('Допустимо від 1 до 1000 студентів.')
                institutions = {i.slug: i for i in Institution.objects.filter(is_active=True)}
                usernames = [r['username'].strip() for r in rows]
                if not all(usernames) or len(set(usernames)) != len(usernames):
                    raise ValueError('Порожні або повторні логіни.')
                if User.objects.filter(username__in=usernames).exists():
                    raise ValueError('Один із логінів вже існує.')
                for row in rows:
                    if row['institution_slug'].strip() not in institutions:
                        raise ValueError('Невідомий заклад: ' + row['institution_slug'])
                    if len(row['username'].strip()) > 150:
                        raise ValueError('Задовгий логін.')
                credentials = []
                alphabet = string.ascii_letters + string.digits + '!@#%'
                with transaction.atomic():
                    for row in rows:
                        password = ''.join(secrets.choice(alphabet) for _ in range(16))
                        user = User.objects.create_user(
                            username=row['username'].strip(), password=password,
                            first_name=row['first_name'].strip()[:150],
                            last_name=row['last_name'].strip()[:150])
                        institution = institutions[row['institution_slug'].strip()]
                        profile = StudentProfile.objects.create(user=user, active_institution=institution)
                        profile.institutions.add(institution)
                        credentials.append([user.username, password, user.first_name,
                                            user.last_name, institution.slug])
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(['username', 'temporary_password', 'first_name', 'last_name', 'institution_slug'])
                writer.writerows(credentials)
                response = HttpResponse('\ufeff' + output.getvalue(), content_type='text/csv; charset=utf-8')
                response['Content-Disposition'] = 'attachment; filename="student_credentials.csv"'
                response['Cache-Control'] = 'no-store'
                return response
            except (UnicodeDecodeError, ValueError, KeyError) as exc:
                form.add_error('csv_file', str(exc))
        return render(request, 'admin/library/import_students.html', {
            **self.admin_site.each_context(request), 'title': 'Імпорт студентів',
            'form': form, 'opts': self.model._meta,
        })

admin.site.unregister(User)
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (StudentProfileInline,)
    list_display = ('username', 'first_name', 'last_name', 'is_active', 'is_staff')
