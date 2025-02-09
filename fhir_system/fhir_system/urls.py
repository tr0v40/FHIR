from django.contrib import admin
from django.urls import path, include
from core.views import home  # Certifique-se de que a view `home` está correta
from django.contrib.auth import views as auth_views  # Importa views padrão de autenticação

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),  # Página inicial
    path('core/', include('core.urls')),  # Inclui as rotas do app core
    path('accounts/', include('django.contrib.auth.urls')),  # Inclui URLs padrão do Django para login/logout
]
