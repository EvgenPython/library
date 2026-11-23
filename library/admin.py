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
from django.db.models import Count, Max, Q
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import path, reverse
from django.utils.html import format_html
from .models import (Institution, Subject, Book, StudentProfile, StudentWorkArchive,
                     TeacherProfile, StudentActivity, BookAudit)

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
    list_display = ('title', 'author', 'subject', 'uploaded_by', 'is_published', 'added_at')
    readonly_fields = ('uploaded_by', 'added_at')
    list_filter = ('subject__institution', 'is_published')
    search_fields = ('title', 'author', 'subject__title')
    autocomplete_fields = ('subject',)
    list_editable = ('is_published',)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)
        BookAudit.log(request.user, BookAudit.EDITED if change else BookAudit.ADDED, obj)

    def delete_model(self, request, obj):
        BookAudit.log(request.user, BookAudit.DELETED, obj)
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset.select_related('subject'):
            BookAudit.log(request.user, BookAudit.DELETED, obj)
        super().delete_queryset(request, queryset)

@admin.register(StudentWorkArchive)
class StudentWorkArchiveAdmin(admin.ModelAdmin):
    list_display = ('title', 'work_type', 'subject', 'group', 'year', 'is_published')
    list_filter = ('work_type', 'year', 'group', 'subject__institution', 'is_published')
    search_fields = ('title', 'group', 'subject__title', 'description')
    autocomplete_fields = ('subject',)
    list_editable = ('is_published',)

class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    extra = 0
    max_num = 1
    can_delete = False
    filter_horizontal = ('institutions',)

class ImportForm(forms.Form):
    csv_file = forms.FileField(label='CSV-файл студентів')

class TeacherProfileInline(admin.StackedInline):
    model = TeacherProfile
    extra = 0
    max_num = 1
    can_delete = False
    filter_horizontal = ('subjects',)


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'assigned_subjects')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    autocomplete_fields = ('user',)
    filter_horizontal = ('subjects',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('subjects')

    @admin.display(description='Закріплені дисципліни')
    def assigned_subjects(self, obj):
        return ', '.join(subject.title for subject in obj.subjects.all()) or 'Не призначено'


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'active_institution', 'login_count', 'last_login_event',
                    'page_views', 'download_requests', 'activity_link')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'active_institution').annotate(
            _login_count=Count('user__library_activity',
                filter=Q(user__library_activity__action=StudentActivity.LOGIN), distinct=True),
            _page_views=Count('user__library_activity',
                filter=Q(user__library_activity__action__in=[
                    StudentActivity.CATALOG, StudentActivity.SUBJECT, StudentActivity.REPOSITORY,
                ]), distinct=True),
            _download_requests=Count('user__library_activity',
                filter=Q(user__library_activity__action__in=[
                    StudentActivity.BOOK_DOWNLOAD, StudentActivity.ARCHIVE_DOWNLOAD,
                ]), distinct=True),
            _last_login_event=Max('user__library_activity__created_at',
                filter=Q(user__library_activity__action=StudentActivity.LOGIN)),
        )

    @admin.display(description='Входів', ordering='_login_count')
    def login_count(self, obj):
        return obj._login_count

    @admin.display(description='Останній вхід', ordering='_last_login_event')
    def last_login_event(self, obj):
        return obj._last_login_event or '—'

    @admin.display(description='Переглядів сторінок', ordering='_page_views')
    def page_views(self, obj):
        return obj._page_views

    @admin.display(description='Запитів на файли', ordering='_download_requests')
    def download_requests(self, obj):
        return obj._download_requests

    @admin.display(description='Історія')
    def activity_link(self, obj):
        url = reverse('admin:library_studentactivity_changelist')
        return format_html('<a href="{}?user__id__exact={}">Переглянути</a>', url, obj.user_id)
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
    inlines = (StudentProfileInline, TeacherProfileInline,)
    list_display = ('username', 'first_name', 'last_name', 'is_active', 'is_staff')


@admin.register(StudentActivity)
class StudentActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'item_title', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'item_title')
    date_hierarchy = 'created_at'
    readonly_fields = ('user', 'action', 'item_title', 'created_at')
    list_select_related = ('user',)
    ordering = ('-created_at',)

    def lookup_allowed(self, lookup, value, request=None):
        return lookup == 'user__id__exact' or super().lookup_allowed(lookup, value, request)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BookAudit)
class BookAuditAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'actor_name', 'action', 'book_title', 'subject_title', 'book_id')
    list_filter = ('action', 'created_at')
    search_fields = ('actor_name', 'book_title', 'subject_title')
    readonly_fields = ('actor', 'actor_name', 'action', 'book_id', 'book_title',
                       'subject_title', 'created_at')
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
