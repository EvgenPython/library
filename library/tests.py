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
