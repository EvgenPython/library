import io
import zipfile
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from .models import Institution, Subject, Book, StudentProfile, StudentWorkArchive

class AccessTests(TestCase):
    def setUp(self):
        college = Institution.objects.create(name='Коледж', slug='college')
        other = Institution.objects.create(name='Університет', slug='university')
        s1 = Subject.objects.create(institution=college, title='Python')
        s2 = Subject.objects.create(institution=other, title='Дизайн')
        self.book = Book.objects.create(subject=s1, title='Python', file=SimpleUploadedFile('a.pdf', b'PDF test'))
        self.other_book = Book.objects.create(subject=s2, title='Design', file=SimpleUploadedFile('b.pdf', b'PDF test'))
        self.user = User.objects.create_user(username='student', password='LongPassword123!')
        profile = StudentProfile.objects.create(user=self.user, active_institution=college)
        profile.institutions.add(college)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as z:
            z.writestr('work.txt', 'demo')
        self.work = StudentWorkArchive.objects.create(subject=s1, title='Курсова', group='КНК-41', year=2026,
            file=SimpleUploadedFile('works.zip', buffer.getvalue()))

    def test_home_requires_login_to_browse(self):
        self.assertContains(self.client.get(reverse('home')), 'Вхід до системи')
        self.assertEqual(self.client.get(reverse('catalog')).status_code, 302)
        self.assertEqual(self.client.get(reverse('works_repository')).status_code, 302)

    def test_login(self):
        response = self.client.post(reverse('home'), {'username':'student','password':'LongPassword123!'})
        self.assertRedirects(response, reverse('catalog'))

    def test_restricted_downloads(self):
        self.assertEqual(self.client.get(reverse('download_book', args=[self.book.pk])).status_code, 302)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('download_book', args=[self.other_book.pk])).status_code, 404)
        response = self.client.get(reverse('download_work_archive', args=[self.work.pk]))
        self.assertEqual(response.status_code, 200)
        response.close()


from .models import TeacherProfile, StudentActivity, BookAudit


class TeacherPortalTests(TestCase):
    def setUp(self):
        self.college = Institution.objects.create(name='Коледж', slug='college')
        self.assigned = Subject.objects.create(institution=self.college, title='Python')
        self.other = Subject.objects.create(institution=self.college, title='Design')
        self.teacher_user = User.objects.create_user(username='teacher', password='StrongPassword123!')
        self.teacher = TeacherProfile.objects.create(user=self.teacher_user)
        self.teacher.subjects.add(self.assigned)
        self.client.force_login(self.teacher_user)

    def test_teacher_can_open_own_dashboard_but_not_admin(self):
        self.assertEqual(self.client.get(reverse('teacher_dashboard')).status_code, 200)
        self.assertNotEqual(self.client.get(reverse('admin:index')).status_code, 200)

    def test_teacher_upload_only_assigned_subject(self):
        response = self.client.post(reverse('teacher_add_book'), {
            'subject': self.assigned.pk,
            'title': 'Вступ до Python',
            'author': 'Професор',
            'description': 'Навчальні матеріали',
            'file': SimpleUploadedFile('book.pdf', b'%PDF-1.4 example'),
        })
        self.assertRedirects(response, reverse('teacher_dashboard'))
        book = Book.objects.get(title='Вступ до Python')
        self.assertEqual(book.uploaded_by, self.teacher_user)
        self.assertTrue(book.is_published)
        self.assertEqual(BookAudit.objects.filter(
            book_id=book.pk, actor=self.teacher_user, action=BookAudit.ADDED).count(), 1)

    def test_teacher_cannot_upload_to_unassigned_subject(self):
        response = self.client.post(reverse('teacher_add_book'), {
            'subject': self.other.pk,
            'title': 'Restricted',
            'author': 'X',
            'file': SimpleUploadedFile('book.pdf', b'%PDF-1.4 example'),
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Book.objects.filter(title='Restricted').exists())

    def test_teacher_cannot_edit_other_users_books(self):
        admin_book = Book.objects.create(
            subject=self.assigned, title='Admin material',
            file=SimpleUploadedFile('admin.pdf', b'%PDF-1.4 example'))
        self.assertEqual(self.client.get(reverse('teacher_edit_book', args=[admin_book.pk])).status_code, 404)

    def test_teacher_cannot_edit_after_subject_revoked(self):
        book = Book.objects.create(
            subject=self.assigned, title='Uploaded',
            uploaded_by=self.teacher_user,
            file=SimpleUploadedFile('teacher.pdf', b'%PDF-1.4 example'))
        self.teacher.subjects.clear()
        self.assertEqual(self.client.get(reverse('teacher_edit_book', args=[book.pk])).status_code, 404)

    def test_student_cannot_open_teacher_portal(self):
        user = User.objects.create_user(username='student2', password='StrongPassword123!')
        StudentProfile.objects.create(user=user)
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse('teacher_dashboard')).status_code, 403)
        self.assertEqual(self.client.get(reverse('teacher_add_book')).status_code, 403)

    def test_teacher_logs_in_to_own_cabinet(self):
        self.client.logout()
        response = self.client.post(reverse('home'), {
            'username': 'teacher', 'password': 'StrongPassword123!',
        })
        self.assertRedirects(response, reverse('teacher_dashboard'))


class StudentActivityTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name='Коледж', slug='college')
        self.subject = Subject.objects.create(institution=self.institution, title='Python')
        self.student = User.objects.create_user(username='studentlog', password='StrongPassword123!')
        profile = StudentProfile.objects.create(user=self.student, active_institution=self.institution)
        profile.institutions.add(self.institution)
        self.book = Book.objects.create(
            subject=self.subject, title='Книга Python',
            file=SimpleUploadedFile('testbook.pdf', b'%PDF-1.4 demo'))

    def test_student_visits_and_download_requests_recorded(self):
        self.assertTrue(self.client.login(username='studentlog', password='StrongPassword123!'))
        self.assertEqual(self.client.get(reverse('catalog')).status_code, 200)
        self.assertEqual(self.client.get(reverse('subject_detail', args=[self.subject.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse('works_repository')).status_code, 200)
        response = self.client.get(reverse('download_book', args=[self.book.pk]))
        self.assertEqual(response.status_code, 200)
        response.close()
        activities = StudentActivity.objects.filter(user=self.student)
        self.assertEqual(activities.filter(action=StudentActivity.LOGIN).count(), 1)
        self.assertEqual(activities.filter(action=StudentActivity.SUBJECT,
                                           item_title__contains='Python').count(), 1)
        self.assertEqual(activities.filter(action=StudentActivity.BOOK_DOWNLOAD,
                                           item_title='Книга Python').count(), 1)
        self.assertEqual(activities.count(), 5)

    def test_admin_can_view_student_statistics(self):
        self.assertTrue(self.client.login(username='studentlog', password='StrongPassword123!'))
        self.client.get(reverse('catalog'))
        director = User.objects.create_superuser(username='director', password='StrongPassword123!')
        self.client.force_login(director)
        response = self.client.get(reverse('admin:library_studentprofile_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'studentlog')
        self.assertContains(response, 'Переглянути')
        self.assertEqual(StudentActivity.objects.filter(user=director).count(), 0)

    def test_non_superuser_staff_cannot_open_admin(self):
        user = User.objects.create_user(username='staffuser', password='StrongPassword123!', is_staff=True)
        self.client.force_login(user)
        self.assertNotEqual(self.client.get(reverse('admin:index')).status_code, 200)
