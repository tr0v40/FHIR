from django.contrib import admin
from django.urls import path, include
from core.views import home  # View da página inicial
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),  # Página inicial
    path('core/', include('core.urls')),  # Inclui as URLs do app "core"
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
