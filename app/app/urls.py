from datetime import datetime
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LoginView, LogoutView
from authentication import forms, views
from authentication import views as viewHome

from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('logout/', LogoutView.as_view(next_page='/login/'), name='logout'),
    path('admin/', admin.site.urls),
    path('', include('authentication.urls')),
    path('home/', include('authentication.urls')),
    
    # Rutas para la administración de catalogos
    path('administracion/', include('administracion.urls')),
    
    path('usuarios/', views.user_list, name='user_list'),
    path('',
         LoginView.as_view
         (
             template_name='authentication/login.html',
             authentication_form=forms.BootstrapAuthenticationForm,
             extra_context={
                 'title': 'Log in',
                 'year': datetime.now().year,
             }
         ),
         name='login'),
         path('login/',viewHome.login),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT, )