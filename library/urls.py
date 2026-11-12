from django.urls import path
from django.contrib.auth.views import LoginView
from . import views

urlpatterns = [
    path('', LoginView.as_view(template_name='library/landing.html', redirect_authenticated_user=True), name='home'),
    path('catalog/', views.catalog, name='catalog'),
    path('institution/select/', views.select_institution, name='select_institution'),
    path('subjects/<int:pk>/', views.subject_detail, name='subject_detail'),
    path('books/<int:pk>/download/', views.download_book, name='download_book'),
    path('repository/', views.works_repository, name='works_repository'),
    path('repository/<int:pk>/download/', views.download_work_archive, name='download_work_archive'),
]
