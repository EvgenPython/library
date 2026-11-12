from pathlib import Path
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.db.models import Count, Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .models import Institution, Subject, Book, StudentProfile, StudentWorkArchive

def accessible_institutions(request):
    if request.user.is_staff:
        return Institution.objects.filter(is_active=True)
    profile = StudentProfile.objects.filter(user=request.user).first()
    if profile is None:
        return Institution.objects.none()
    return profile.institutions.filter(is_active=True)

def context_for(request):
    institutions = accessible_institutions(request)
    profile = StudentProfile.objects.filter(user=request.user).first()
    active = None
    if profile and profile.active_institution_id:
        active = institutions.filter(pk=profile.active_institution_id).first()
    return institutions, active or institutions.first(), profile

@login_required
def catalog(request):
    institutions, active, profile = context_for(request)
    q = request.GET.get('q', '').strip()[:100]
    subjects = Subject.objects.none()
    if active:
        subjects = Subject.objects.filter(institution=active, is_active=True).annotate(
            book_count=Count('books', filter=Q(books__is_published=True)))
        if q:
            subjects = subjects.filter(Q(title__icontains=q) | Q(description__icontains=q))
    return render(request, 'library/home.html', {
        'institutions': institutions, 'active_institution': active,
        'profile': profile, 'subjects': subjects, 'q': q,
    })

@login_required
@require_POST
def select_institution(request):
    institution = get_object_or_404(accessible_institutions(request), pk=request.POST.get('institution_id'))
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    profile.active_institution = institution
    profile.save(update_fields=['active_institution'])
    return redirect('catalog')

@login_required
def subject_detail(request, pk):
    institutions, active, profile = context_for(request)
    subject = get_object_or_404(Subject, pk=pk, is_active=True, institution__in=institutions)
    return render(request, 'library/subject.html', {
        'subject': subject, 'books': subject.books.filter(is_published=True),
        'institutions': institutions, 'active_institution': active, 'profile': profile,
    })

@login_required
def download_book(request, pk):
    book = get_object_or_404(Book.objects.select_related('subject'),
        pk=pk, is_published=True, subject__is_active=True,
        subject__institution__in=accessible_institutions(request))
    try:
        stream = book.file.open('rb')
    except (FileNotFoundError, OSError, ValueError):
        raise Http404('Файл недоступний')
    response = FileResponse(stream, as_attachment=True,
                            filename=f'book-{book.pk}{Path(book.file.name).suffix.lower()}',
                            content_type='application/octet-stream')
    response['Cache-Control'] = 'private, no-store'
    response['X-Content-Type-Options'] = 'nosniff'
    return response

@login_required
def works_repository(request):
    institutions, active, profile = context_for(request)
    base = StudentWorkArchive.objects.filter(is_published=True, subject__is_active=True,
                                             subject__institution__in=institutions)
    archives = base.select_related('subject', 'subject__institution')
    institution = request.GET.get('institution', '')
    if institution.isdecimal():
        archives = archives.filter(subject__institution_id=institution)
    work_type = request.GET.get('type', '')
    if work_type in ('course', 'diploma'):
        archives = archives.filter(work_type=work_type)
    subject = request.GET.get('subject', '')
    if subject.isdecimal():
        archives = archives.filter(subject_id=subject)
    year = request.GET.get('year', '')
    if year.isdecimal():
        archives = archives.filter(year=int(year))
    group = request.GET.get('group', '').strip()[:80]
    if group:
        archives = archives.filter(group__iexact=group)
    q = request.GET.get('q', '').strip()[:100]
    if q:
        archives = archives.filter(Q(title__icontains=q) | Q(description__icontains=q))
    return render(request, 'library/repository.html', {
        'archives': archives[:200], 'institutions': institutions,
        'subjects': Subject.objects.filter(is_active=True, institution__in=institutions),
        'years': base.order_by('-year').values_list('year', flat=True).distinct(),
        'groups': base.order_by('group').values_list('group', flat=True).distinct(),
        'selected': request.GET, 'active_institution': active, 'profile': profile,
    })

@login_required
def download_work_archive(request, pk):
    work = get_object_or_404(StudentWorkArchive.objects.select_related('subject'), pk=pk,
        is_published=True, subject__is_active=True,
        subject__institution__in=accessible_institutions(request))
    try:
        stream = work.file.open('rb')
    except (FileNotFoundError, OSError, ValueError):
        raise Http404('Архів недоступний')
    response = FileResponse(stream, as_attachment=True,
        filename=f'works-{work.pk}-{work.year}.zip', content_type='application/zip')
    response['Cache-Control'] = 'private, no-store'
    response['X-Content-Type-Options'] = 'nosniff'
    return response

class StudentPasswordChangeView(PasswordChangeView):
    def form_valid(self, form):
        result = super().form_valid(form)
        StudentProfile.objects.filter(user=self.request.user).update(must_change_password=False)
        return result
