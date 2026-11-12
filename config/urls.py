from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from library.views import StudentPasswordChangeView

admin.site.site_header = 'Електронна бібліотека — адміністрування'
admin.site.site_title = 'IT STEP Бібліотека'
admin.site.index_title = 'Керування бібліотекою'
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='library/landing.html', redirect_authenticated_user=True), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/password-change/', StudentPasswordChangeView.as_view(template_name='registration/password_change.html', success_url='/catalog/'), name='password_change'),
    path('', include('library.urls')),
]
