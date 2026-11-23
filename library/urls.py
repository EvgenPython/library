from django.urls import path
from .teacher_views import teacher_dashboard, teacher_add_book, teacher_edit_book
from . import views

urlpatterns = [
    path('', views.RoleLoginView.as_view(), name='home'),
    path('teacher/', teacher_dashboard, name='teacher_dashboard'),
    path('teacher/books/add/', teacher_add_book, name='teacher_add_book'),
    path('teacher/books/<int:pk>/edit/', teacher_edit_book, name='teacher_edit_book'),
    path('catalog/', views.catalog, name='catalog'),
    path('institution/select/', views.select_institution, name='select_institution'),
    path('subjects/<int:pk>/', views.subject_detail, name='subject_detail'),
    path('books/<int:pk>/download/', views.download_book, name='download_book'),
    path('repository/', views.works_repository, name='works_repository'),
    path('repository/<int:pk>/download/', views.download_work_archive, name='download_work_archive'),
]
