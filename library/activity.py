from .models import StudentActivity, StudentProfile, TeacherProfile


def track_student(request, action, item_title=''):
    """Store only student activity after successful authorized actions, without IP/UA/query strings."""
    user = request.user
    if not user.is_authenticated or user.is_superuser or user.is_staff:
        return
    if TeacherProfile.objects.filter(user_id=user.pk).exists():
        return
    if StudentProfile.objects.filter(user_id=user.pk).exists():
        StudentActivity.objects.create(user=user, action=action, item_title=str(item_title)[:350])
