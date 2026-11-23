from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from library.views import StudentPasswordChangeView, RoleLoginView

admin.site.site_header = 'Електронна бібліотека — адміністрування'
admin.site.site_title = 'IT STEP Бібліотека'
admin.site.index_title = 'Керування бібліотекою'
# /admin/ is reserved for the director/superusers only, not teacher accounts.
admin.site.has_permission = lambda request: request.user.is_active and request.user.is_superuser
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', RoleLoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/password-change/', StudentPasswordChangeView.as_view(template_name='registration/password_change.html', success_url='/catalog/'), name='password_change'),
    path('', include('library.urls')),
]
