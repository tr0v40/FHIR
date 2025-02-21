from django.contrib import admin
from django.urls import path, include  # Certifique-se de que 'path' está importado corretamente
from core.views import home  # Importando a view `home` do app core
from django.conf import settings
from django.conf.urls.static import static
from core import views 
from django.contrib.auth.views import LoginView


urlpatterns = [
    path('', LoginView.as_view(), name='home'),
    path('admin/', admin.site.urls),  # Rota para o painel de administração
    
    # path('', home, name='home'),  # Página inicial (home)
    # path('core/', include('core.urls')),  # Inclui as rotas do app core
    path('accounts/', include('django.contrib.auth.urls')),  # URLs padrão de login/logout
    path('register/', views.register, name='register'),
    path('tratamentos/', views.tratamentos, name='tratamentos'),
    path('tratamento/<int:tratamento_id>/', views.detalhes_tratamentos, name='detalhes_tratamentos'),
    path("evidencias-clinicas/<int:tratamento_id>/", views.evidencias_clinicas, name="evidencias_clinicas"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)