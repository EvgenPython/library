from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import TeacherBookForm
from .models import Book, BookAudit, TeacherProfile


def teacher_for(request):
    if request.user.is_superuser or request.user.is_staff:
        raise PermissionDenied('Кабінет доступний лише викладачам.')
    try:
        return TeacherProfile.objects.get(user=request.user)
    except TeacherProfile.DoesNotExist:
        raise PermissionDenied('Немає профілю викладача.')


@login_required
def teacher_dashboard(request):
    teacher = teacher_for(request)
    subjects = teacher.subjects.select_related('institution').order_by('institution__name', 'title')
    books = Book.objects.filter(uploaded_by=request.user, subject__in=teacher.subjects.all()) \
        .select_related('subject', 'subject__institution').order_by('-added_at')
    return render(request, 'library/teacher_dashboard.html',
                  {'teacher_subjects': subjects, 'teacher_books': books})


@login_required
@require_http_methods(['GET', 'POST'])
def teacher_add_book(request):
    teacher = teacher_for(request)
    form = TeacherBookForm(request.POST or None, request.FILES or None, teacher=teacher)
    if request.method == 'POST' and form.is_valid():
        book = form.save(commit=False)
        book.uploaded_by = request.user
        book.is_published = True
        book.save()
        BookAudit.log(request.user, BookAudit.ADDED, book)
        messages.success(request, 'Літературу додано до каталогу.')
        return redirect('teacher_dashboard')
    return render(request, 'library/teacher_book_form.html',
                  {'form': form, 'editing': False})


@login_required
@require_http_methods(['GET', 'POST'])
def teacher_edit_book(request, pk):
    teacher = teacher_for(request)
    book = get_object_or_404(Book, pk=pk, uploaded_by=request.user,
                             subject__in=teacher.subjects.all())
    form = TeacherBookForm(request.POST or None, request.FILES or None,
                           instance=book, teacher=teacher)
    if request.method == 'POST' and form.is_valid():
        book = form.save()
        BookAudit.log(request.user, BookAudit.EDITED, book)
        messages.success(request, 'Зміни збережено.')
        return redirect('teacher_dashboard')
    return render(request, 'library/teacher_book_form.html',
                  {'form': form, 'editing': True, 'book': book})
