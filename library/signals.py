from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from .models import StudentActivity, StudentProfile, TeacherProfile


@receiver(user_logged_in)
def record_student_login(sender, request, user, **kwargs):
    if user.is_superuser or user.is_staff:
        return
    if TeacherProfile.objects.filter(user_id=user.pk).exists():
        return
    if StudentProfile.objects.filter(user_id=user.pk).exists():
        StudentActivity.objects.create(user=user, action=StudentActivity.LOGIN)
