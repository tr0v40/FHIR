from django.contrib import admin
from django.urls import path, include  # Certifique-se de que 'path' está importado corretamente
from core.views import home  # Importando a view `home` do app core
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),  # Rota para o painel de administração
    path('', home, name='home'),  # Página inicial (home)
    path('core/', include('core.urls')),  # Inclui as rotas do app core
    path('accounts/', include('django.contrib.auth.urls')),  # URLs padrão de login/logout
]

# Serve os arquivos estáticos durante o desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Serve os arquivos de mídia durante o desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
